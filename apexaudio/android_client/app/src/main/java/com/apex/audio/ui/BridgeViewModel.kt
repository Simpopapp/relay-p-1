package com.apex.audio.ui

import android.Manifest
import android.content.pm.PackageManager
import android.app.Application
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.os.IBinder
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.apex.audio.network.BridgeState
import com.apex.audio.service.AudioBridgeService
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

enum class TransportMode { USB_ADB, LAN }

data class BridgeUiState(
    val host: String = "127.0.0.1",
    val transportMode: TransportMode = TransportMode.USB_ADB,
    val state: BridgeState = BridgeState.DISCONNECTED,
    val rttMs: Float = -1f,
    val sampleRateHz: Int = 48000,
    val gain: Float = 1.0f,
    val muted: Boolean = false,
    val bufferHealthPercent: Int = 0,
    val bufferFrames: Int = 0,
    val bufferDrops: Int = 0,
    val permissionsGranted: Boolean = false,
)

/**
 * Estado da UI (PRD §8.1). Faz binding ao AudioBridgeService e publica
 * telemetria em tempo real via StateFlow.
 *
 * Ciclo de vida (Fase 6 do roadmap central): o binder NUNCA é descartado na
 * desconexão do usuário — o reconectar reutiliza a referência e chama
 * `connect()` de novo. O CONECTAR só dispara com as permissões concedidas.
 */
class BridgeViewModel(application: Application) : AndroidViewModel(application) {

    private val _ui = MutableStateFlow(BridgeUiState())
    val ui: StateFlow<BridgeUiState> = _ui

    private var service: AudioBridgeService? = null
    private var bound = false
    private var connectJob: Job? = null

    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, binder: IBinder?) {
            service = (binder as AudioBridgeService.LocalBinder).service
            bound = true
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            // Processo do serviço morreu: solta só a referência. O binding
            // (BIND_AUTO_CREATE) continua registrado e o sistema recria o
            // serviço, chamando onServiceConnected de novo.
            service = null
        }
    }

    init {
        val app = getApplication<Application>()
        bound = app.bindService(
            Intent(app, AudioBridgeService::class.java),
            connection, Context.BIND_AUTO_CREATE,
        )
        // telemetria: 4 Hz
        viewModelScope.launch {
            while (true) {
                delay(250)
                val svc = service
                if (svc != null) {
                    // Não deixa a telemetria apagar o CONNECTING publicado
                    // enquanto o binder ainda não chegou.
                    val state = if (connectJob?.isActive == true &&
                        svc.currentState == BridgeState.DISCONNECTED
                    ) BridgeState.CONNECTING else svc.currentState
                    _ui.value = _ui.value.copy(
                        state = state,
                        rttMs = svc.currentRtt,
                        bufferHealthPercent = svc.bufferHealthPercent,
                        bufferFrames = svc.bufferFrames,
                        bufferDrops = svc.bufferDrops,
                    )
                }
            }
        }
    }

    fun refreshPermissions() {
        val app = getApplication<Application>()
        // Gate do CONECTAR = SOMENTE microfone (D4): o FGS funciona sem
        // notificações; negar POST_NOTIFICATIONS não pode travar o app.
        val granted =
            app.checkSelfPermission(Manifest.permission.RECORD_AUDIO) ==
                PackageManager.PERMISSION_GRANTED
        _ui.value = _ui.value.copy(permissionsGranted = granted)
    }

    fun setHost(host: String) {
        _ui.value = _ui.value.copy(host = host)
    }

    fun setTransportMode(mode: TransportMode) {
        _ui.value = _ui.value.copy(transportMode = mode)
    }

    fun toggleConnect() {
        val current = _ui.value
        if (current.state != BridgeState.DISCONNECTED) {
            connectJob?.cancel()
            connectJob = null
            service?.disconnect()
            _ui.value = _ui.value.copy(state = BridgeState.DISCONNECTED)
            return
        }

        refreshPermissions()
        // idempotência: sem permissão, ou já conectando, não dispara de novo
        if (!_ui.value.permissionsGranted || connectJob?.isActive == true) return

        val app = getApplication<Application>()
        val host = if (current.transportMode == TransportMode.USB_ADB) {
            "127.0.0.1"
        } else {
            current.host
        }
        _ui.value = _ui.value.copy(host = host, state = BridgeState.CONNECTING)

        connectJob = viewModelScope.launch {
            app.startForegroundService(Intent(app, AudioBridgeService::class.java))
            var tries = 0
            while (service == null && tries < 20) {
                delay(100)
                tries++
            }
            val svc = service
            if (svc == null) {
                app.stopService(Intent(app, AudioBridgeService::class.java))
                _ui.value = _ui.value.copy(state = BridgeState.DISCONNECTED)
                return@launch
            }
            if (svc.currentState == BridgeState.DISCONNECTED) {
                svc.connect(host, current.transportMode == TransportMode.LAN)
            }
        }
    }

    fun setGain(gain: Float) {
        _ui.value = _ui.value.copy(gain = gain)
        service?.setMicGain(gain)
    }

    fun setMuted(muted: Boolean) {
        _ui.value = _ui.value.copy(muted = muted)
        service?.setMicMuted(muted)
    }

    override fun onCleared() {
        if (bound) {
            getApplication<Application>().unbindService(connection)
            bound = false
        }
        super.onCleared()
    }
}
