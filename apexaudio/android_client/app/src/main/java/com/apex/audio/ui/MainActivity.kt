package com.apex.audio.ui

import android.Manifest
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.apex.audio.network.BridgeState

/**
 * Tela única Compose (PRD §8.1): dark monocromático, painel de conexão,
 * telemetria em tempo real e controles rápidos (ganho/mute).
 *
 * Fase 6: RECORD_AUDIO (+ POST_NOTIFICATIONS em SDK 33+) é pedido em runtime
 * ANTES do primeiro CONECTAR; o botão fica desabilitado e com aviso até a
 * permissão ser concedida (negação não gera crash nem loop de pedido).
 */
class MainActivity : ComponentActivity() {

    private val viewModel: BridgeViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            PermissionsGate(viewModel)
            Surface(color = Color(0xFF0B0D10)) {
                BridgeScreen(viewModel)
            }
        }
    }

    override fun onResume() {
        super.onResume()
        viewModel.refreshPermissions()
    }
}

@Composable
private fun PermissionsGate(viewModel: BridgeViewModel) {
    val permissionsLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) {
        // concede ou nega: reavalia o estado (habilita o CONECTAR se OK)
        viewModel.refreshPermissions()
    }

    LaunchedEffect(Unit) {
        viewModel.refreshPermissions()
        if (!viewModel.ui.value.permissionsGranted) {
            permissionsLauncher.launch(
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    arrayOf(
                        Manifest.permission.RECORD_AUDIO,
                        Manifest.permission.POST_NOTIFICATIONS,
                    )
                } else {
                    arrayOf(Manifest.permission.RECORD_AUDIO)
                }
            )
        }
    }
}

private val Green = Color(0xFF7BE495)
private val Red = Color(0xFFFF6B6B)
private val Amber = Color(0xFFFFC15E)
private val Ink = Color(0xFFE6E9EF)
private val Muted = Color(0xFF8A93A5)

@Composable
fun BridgeScreen(viewModel: BridgeViewModel) {
    val ui by viewModel.ui.collectAsState()
    val statusColor = when (ui.state) {
        BridgeState.STREAMING -> Green
        BridgeState.CONNECTING, BridgeState.HANDSHAKE, BridgeState.RECONNECTING -> Amber
        BridgeState.DISCONNECTED -> Red
    }
    val healthColor = when {
        ui.bufferDrops > 0 -> Red
        ui.bufferFrames >= 3 -> Amber
        else -> Green
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0B0D10))
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("APEXAUDIO", color = Ink, fontSize = 28.sp, fontFamily = FontFamily.Monospace)
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .width(10.dp)
                    .height(10.dp)
                    .background(statusColor, RoundedCornerShape(5.dp))
            )
            Spacer(Modifier.width(8.dp))
            Text(
                when (ui.state) {
                    BridgeState.STREAMING -> "ONLINE"
                    BridgeState.CONNECTING -> "CONNECTING"
                    BridgeState.HANDSHAKE -> "CONNECTING"
                    BridgeState.RECONNECTING -> "CONNECTING"
                    BridgeState.DISCONNECTED -> "OFFLINE"
                },
                color = statusColor,
                fontFamily = FontFamily.Monospace,
            )
        }

        // --- Painel de conexão ---
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Modo USB (ADB)", color = Ink)
            Spacer(Modifier.width(8.dp))
            Switch(
                checked = ui.transportMode == TransportMode.LAN,
                onCheckedChange = { lan ->
                    viewModel.setTransportMode(if (lan) TransportMode.LAN else TransportMode.USB_ADB)
                },
                colors = SwitchDefaults.colors(checkedTrackColor = Green),
            )
            Spacer(Modifier.width(8.dp))
            Text("Modo LAN (Wi-Fi)", color = Ink)
        }
        if (ui.transportMode == TransportMode.LAN) {
            TextField(
                value = ui.host,
                onValueChange = viewModel::setHost,
                label = { Text("Host do PC") },
                singleLine = true,
                colors = TextFieldDefaults.colors(
                    focusedTextColor = Ink,
                    unfocusedTextColor = Ink,
                ),
                modifier = Modifier.fillMaxWidth(),
            )
        }

        Button(
            onClick = viewModel::toggleConnect,
            enabled = ui.permissionsGranted || ui.state != BridgeState.DISCONNECTED,
            colors = ButtonDefaults.buttonColors(
                containerColor = if (ui.state == BridgeState.DISCONNECTED) Green else Red,
                contentColor = Color.Black,
                disabledContainerColor = Muted,
                disabledContentColor = Color.Black,
            ),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(
                if (ui.state == BridgeState.DISCONNECTED) "CONECTAR" else "DESCONECTAR",
                fontFamily = FontFamily.Monospace,
            )
        }
        if (!ui.permissionsGranted) {
            Text("Permissão de microfone necessária", color = Muted)
        }

        // --- Telemetria ---
        Text(
            "Latency: ${if (ui.rttMs >= 0) "%.1f ms".format(ui.rttMs) else "--"}",
            color = Ink, fontFamily = FontFamily.Monospace,
        )
        Text(
            "${ui.sampleRateHz},000 Hz | 16-bit PCM",
            color = Muted, fontFamily = FontFamily.Monospace,
        )
        Text("Buffer Health", color = Muted, fontFamily = FontFamily.Monospace)
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(8.dp)
                .background(Color(0xFF1A1E26), RoundedCornerShape(4.dp))
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(ui.bufferHealthPercent / 100f)
                    .height(8.dp)
                    .background(healthColor, RoundedCornerShape(4.dp))
            )
        }
        Text(
            "frames: ${ui.bufferFrames} | drops: ${ui.bufferDrops}",
            color = Muted, fontFamily = FontFamily.Monospace, fontSize = 12.sp,
        )

        // --- Controles rápidos ---
        Text("Ganho do microfone: ${"%.2f".format(ui.gain)}x", color = Ink)
        Slider(
            value = ui.gain,
            onValueChange = viewModel::setGain,
            valueRange = 0.0f..2.0f,
        )
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Mudo (microfone)", color = Ink)
            Spacer(Modifier.width(12.dp))
            Switch(
                checked = ui.muted,
                onCheckedChange = viewModel::setMuted,
                colors = SwitchDefaults.colors(checkedTrackColor = Red),
            )
        }
        Text(
            "Fone no celular + microfone virtual no PC: pronto.",
            color = Muted, fontSize = 12.sp,
        )
    }
}
