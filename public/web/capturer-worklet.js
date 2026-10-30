class ApexCapturer extends AudioWorkletProcessor {
 constructor(){super();this.pcm=new ArrayBuffer(960);this.view=new DataView(this.pcm);this.offset=0;this.gain=1;this.mute=false;this.port.onmessage=({data})=>{this.gain=Math.max(0,Math.min(2,data.gain));this.mute=!!data.mute;};}
 process(inputs,outputs){for(const channel of outputs[0]||[])channel.fill(0);const input=inputs[0]?.[0];if(input)for(const sample of input){const v=this.mute?0:Math.max(-1,Math.min(1,sample*this.gain));this.view.setInt16(this.offset*2,Math.round(v*32767),true);if(++this.offset===480){this.port.postMessage(this.pcm,[this.pcm]);this.pcm=new ArrayBuffer(960);this.view=new DataView(this.pcm);this.offset=0;}}return true;}
}
registerProcessor('apex-capturer',ApexCapturer);
