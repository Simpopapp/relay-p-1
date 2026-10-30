class ApexPlayer extends AudioWorkletProcessor {
 constructor(){super();this.queue=[];this.offset=0;this.target=2;this.playing=false;this.ticks=0;this.stable=0;this.port.onmessage=({data})=>{if(data.type==='flush'){this.queue=[];this.offset=0;this.playing=false;this.target=2;return;}if(data.type==='frame'&&data.pcm.byteLength===1920){if(this.queue.length>=4){this.queue.shift();this.offset=0;}this.queue.push(new DataView(data.pcm));}};}
 process(inputs,outputs){const out=outputs[0];for(const c of out)c.fill(0);if(!this.playing&&this.queue.length>=this.target)this.playing=true;
 for(let i=0;i<out[0].length&&this.playing;i++){if(!this.queue.length){this.playing=false;this.target=Math.min(4,this.target+1);this.stable=0;break;}const v=this.queue[0];out[0][i]=v.getInt16(this.offset*4,true)/32768;if(out[1])out[1][i]=v.getInt16(this.offset*4+2,true)/32768;if(++this.offset===480){this.queue.shift();this.offset=0;}}
 if(++this.stable>1875){this.target=Math.max(2,this.target-1);this.stable=0;}if(++this.ticks%20===0)this.port.postMessage({level:this.queue.length,target:this.target,playing:this.playing});return true;}
}
registerProcessor('apex-player',ApexPlayer);
