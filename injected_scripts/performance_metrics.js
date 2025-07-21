(() => {
  try {
    const nav = performance.getEntriesByType("navigation")[0];
    const paints = performance.getEntriesByType("paint");
    const marks = performance.getEntriesByType("mark");
    const measures = performance.getEntriesByType("measure");
    
    // Get LCP from Performance Observer if available
    let lcp = null;
    if (window.lcpValue) {
      lcp = window.lcpValue;
    } else {
      const lcpEntries = paints.filter(p => p.name === "largest-contentful-paint");
      lcp = lcpEntries.length > 0 ? lcpEntries[lcpEntries.length - 1].startTime : null;
    }
    
    const result = {
      // Navigation timing
      ttfb: nav ? nav.responseStart - nav.requestStart : null,
      domContentLoaded: nav ? nav.domContentLoadedEventEnd - nav.startTime : null,
      loadEvent: nav ? nav.loadEventEnd - nav.startTime : null,
      
      // Paint timing
      fcp: paints.find(p => p.name === "first-contentful-paint")?.startTime || null,
      lcp: lcp,
      
      // Additional metrics
      domInteractive: nav ? nav.domInteractive - nav.startTime : null,
      firstPaint: paints.find(p => p.name === "first-paint")?.startTime || null,
      
      // Resource timing
      totalResources: performance.getEntriesByType("resource").length,
      
      // Custom marks and measures
      customMarks: marks.length,
      customMeasures: measures.length,
      
      // Page load time
      pageLoadTime: performance.now(),
      
      // User agent info
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString()
    };
    
    // store for later
    window.__perfMetrics = result;
  } catch (err) {
    window.__perfMetrics = {
      error: err.message,
      timestamp: new Date().toISOString()
    };
  }
})();