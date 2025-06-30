(function() {
  const banner = document.createElement('div');
  banner.textContent = 'Hello world';
  Object.assign(banner.style, {
    position: 'fixed',
    top: '0',
    left: '0',
    width: '100%',
    backgroundColor: 'white',
    color: 'black',
    fontSize: '48px',
    fontWeight: 'bold',
    textAlign: 'center',
    padding: '10px',
    zIndex: '9999',
  });
  document.documentElement.prepend(banner);
  console.log('Hello world banner added to the top of the page');
  console.log("Hello" + window.name || 'unnamed-frame');
})();
