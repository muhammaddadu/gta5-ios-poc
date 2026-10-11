'use strict';
async function check() {
  const result = {browser: navigator.userAgent, secureContext: isSecureContext,
    crossOriginIsolated, sharedArrayBuffer: typeof SharedArrayBuffer !== 'undefined'};
  try {
    result.sharedMemory = new WebAssembly.Memory({initial: 1, maximum: 1, shared: true}).buffer instanceof SharedArrayBuffer;
  } catch (error) {result.sharedMemory = String(error);}
  // Synthetic, asset-free module declaring a single 64-bit memory.
  result.memory64 = WebAssembly.validate(new Uint8Array([0,97,115,109,1,0,0,0,5,3,1,4,0]));
  try {
    const adapter = await navigator.gpu?.requestAdapter();
    result.webgpuAdapter = Boolean(adapter);
    if (adapter) {
      const device = await adapter.requestDevice();
      result.webgpuDevice = true;
      device.destroy();
    }
  } catch (error) {result.webgpuError = String(error);}
  try {
    const status = await (await fetch('/__support/status.json')).json();
    result.gamePresent = status.game_present;
    document.querySelector('#launch').hidden = !status.game_present;
    document.querySelector('#state').textContent = status.game_present ? 'Game inputs found; verify them before launch.' : 'Game inputs missing. Gameplay and IPA build remain blocked.';
    if (status.game_present) {
      const response = await fetch(status.engine_path, {headers: {Range: 'bytes=0-3'}});
      result.engineRangeStatus = response.status;
      result.engineContentRange = response.headers.get('Content-Range');
      const bytes = new Uint8Array(await response.arrayBuffer());
      result.engineMagic = bytes.length === 4 && bytes.every((v, i) => v === [0,97,115,109][i]);
    }
  } catch (error) {result.transportError = String(error);}
  document.querySelector('#report').textContent = JSON.stringify(result, null, 2);
  window.localPortDiagnostics = result;
}
document.querySelector('#check').addEventListener('click', check);
check();
