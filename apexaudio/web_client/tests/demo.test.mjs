import {test} from 'node:test';import assert from 'node:assert/strict';import {DemoSource} from '../demo-source.js';
test('demo: estéreo 1920B, sinal não nulo, RTT simulado',()=>{let pcm,rtt;const s=new DemoSource(p=>pcm=p,r=>rtt=r);s.tick();assert.equal(pcm.length,1920);assert(pcm.some(x=>x!==0));assert(rtt>=10.5&&rtt<=13.5);assert.equal(s.samples,480);s.stop();});
