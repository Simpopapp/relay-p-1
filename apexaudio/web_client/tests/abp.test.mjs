import {test} from 'node:test';import assert from 'node:assert/strict';import * as a from '../abp.js';
const hex=s=>Uint8Array.from(s.split(' ').map(x=>parseInt(x,16)));
for(const [name,type,header,payload] of [
 ['PING',2,'55 aa 02 00 01 00 00 00 e8 03 00 00 00 00 00 00',0],
 ['PONG',3,'55 aa 03 00 01 00 00 00 e8 03 00 00 00 00 00 00',0],
 ['downlink',1,'55 aa 01 00 2a 00 00 00 00 00 00 00 80 07 00 00',1920],
 ['uplink',1,'55 aa 01 01 01 00 00 00 00 00 00 00 c0 03 00 00',960]])test(name,()=>{const expected=new Uint8Array(16+payload);expected.set(hex(header));assert.deepEqual(a.encode(type,name==='uplink'?1:0,name==='downlink'?42:1,new Uint8Array(payload),payload?0:1000),expected);});
test('CONFIG_SYNC byte-exato e parse',()=>{const saved=performance.now;Object.defineProperty(performance,'now',{value:()=>1,configurable:true});try{const p=a.makeConfigSync(48000,2,1920,7);assert.deepEqual(p,hex('55 aa 04 00 07 00 00 00 e8 03 00 00 07 00 00 00 80 bb 00 00 02 80 07'));assert.deepEqual(a.parseConfigSync(a.decode(p)),{sampleRate:48000,channels:2,frameBytes:1920});}finally{Object.defineProperty(performance,'now',{value:saved,configurable:true});}});
test('round trip unsigned e view deslocada',()=>{const p=a.encode(1,1,0xffffffff,hex('01 80 ff 7f'),0xffffffff),b=new Uint8Array(p.length+3);b.set(p,3);assert.deepEqual(a.decode(b.subarray(3)),{packetType:1,channelId:1,seq:4294967295,tsUs:4294967295,payload:hex('01 80 ff 7f')});});
test('stream concatenação e fragmentação em cada byte',()=>{const p=a.encode(1,0,0,new Uint8Array(1920),0),both=new Uint8Array(p.length*2);both.set(p);both.set(p,p.length);assert.equal(a.feedStream(both).frames.length,2);assert.equal(a.feedStream(both).rest.length,0);for(let i=0;i<p.length;i++){assert.equal(a.decode(p.slice(0,i)),null);assert.deepEqual(a.feedStream(p.slice(0,i)),{frames:[],rest:p.slice(0,i)});}});
test('rejeições magic e config',()=>{assert.throws(()=>a.decode(new Uint8Array(16)));assert.throws(()=>a.feedStream(new Uint8Array(16)));assert.throws(()=>a.parseConfigSync({packetType:1,payload:new Uint8Array(7)}));});
