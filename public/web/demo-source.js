export class DemoSource {
 constructor(onFrame,onRtt){this.onFrame=onFrame;this.onRtt=onRtt;this.phase=0;this.samples=0;this.timer=null;}
 tick(){const p=new Uint8Array(1920),v=new DataView(p.buffer);for(let i=0;i<480;i++){const t=this.samples++/48000;this.phase+=2*Math.PI*(440+2*Math.sin(t*2*Math.PI*4))/48000;const value=Math.round(Math.sin(this.phase)*0.12*32767);v.setInt16(i*4,value,true);v.setInt16(i*4+2,Math.round(value*0.96),true);}this.onFrame(p);this.onRtt(12+Math.sin(this.samples/48000)*1.5);}
 start(){if(this.timer!==null)return;this.tick();this.timer=setInterval(()=>this.tick(),10);}
 stop(){clearInterval(this.timer);this.timer=null;}
}
