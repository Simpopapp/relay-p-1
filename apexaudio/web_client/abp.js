export const MAGIC=0xAA55, PACKET_AUDIO=1, PACKET_PING=2, PACKET_PONG=3, PACKET_CONFIG_SYNC=4, CHANNEL_DOWNLINK=0, CHANNEL_UPLINK=1, HEADER_SIZE=16, FRAME_BYTES_DOWNLINK=1920, FRAME_BYTES_UPLINK=960;
const bytes = b => b instanceof Uint8Array ? b : new Uint8Array(b);
export function encode(packetType,channelId,seq,payload,tsUs=performance.now()*1000){
 payload=bytes(payload); const out=new Uint8Array(16+payload.length),v=new DataView(out.buffer);
 v.setUint16(0,MAGIC,true);v.setUint8(2,packetType);v.setUint8(3,channelId);v.setUint32(4,seq>>>0,true);v.setUint32(8,tsUs>>>0,true);v.setUint32(12,payload.length>>>0,true);out.set(payload,16);return out;
}
export function decode(buf){
 buf=bytes(buf);if(buf.length<16)return null;const v=new DataView(buf.buffer,buf.byteOffset,buf.byteLength);
 if(v.getUint16(0,true)!==MAGIC)throw new Error('Magic ABP inválido');const size=v.getUint32(12,true);if(buf.length<16+size)return null;
 return {packetType:v.getUint8(2),channelId:v.getUint8(3),seq:v.getUint32(4,true),tsUs:v.getUint32(8,true),payload:buf.slice(16,16+size)};
}
export function feedStream(buf){buf=bytes(buf);const frames=[];let offset=0;while(offset<buf.length){const f=decode(buf.subarray(offset));if(!f)break;frames.push(f);offset+=16+f.payload.length;}return {frames,rest:buf.slice(offset)};}
export function makeConfigSync(sampleRate,channels,frameBytes,seq){const p=new Uint8Array(7),v=new DataView(p.buffer);v.setUint32(0,sampleRate>>>0,true);v.setUint8(4,channels);v.setUint16(5,frameBytes,true);return encode(4,0,seq,p);}
export function parseConfigSync(frame){if(frame.packetType!==4||frame.payload.length!==7)throw new Error('CONFIG_SYNC inválido');const p=frame.payload,v=new DataView(p.buffer,p.byteOffset,p.byteLength);return {sampleRate:v.getUint32(0,true),channels:v.getUint8(4),frameBytes:v.getUint16(5,true)};}
