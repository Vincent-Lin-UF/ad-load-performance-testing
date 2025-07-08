;(function(userCode){
  try {
    const fe = window.frameElement;
    const me = fe ? `iframe#${fe.id}` : 'top-level';
    console.log(`[DSQ-DBG] running in ${me} @ ${location.href}`);
    console.log('[DSQ-DBG] wrapper executing in frame:', fe && fe.id, location.hostname);

    const sources = Array.from(document.getElementsByTagName('iframe'))
                         .map(f => f.src || '<no‑src>');
    console.log('[DSQ-DBG] child iframes:', sources);

    (new Function(userCode))();
  } catch(e) {
    console.error('[DSQ-DBG] wrapper error', e);
  }
});