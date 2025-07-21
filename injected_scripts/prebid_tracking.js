(function() {
    const frameName = window.name || 'unnamed-frame';
    console.log("Performance Tracker Initialized");

    const pageLoadTime = performance.now();
    console.log("Frame loaded at:", pageLoadTime.toFixed(2), "ms, frame:", frameName);

    window.prebidPerformanceData = {
        frameName: frameName,
        pageLoadTime: pageLoadTime,
        bidWins: [],
        adRenders: [],
        auctions: [],
    };

    window.getPrebidPerformanceSummary = () => window.prebidPerformanceData;

    function waitForPrebid() {
        if (typeof window.pbjs !== 'undefined' &&
            typeof window.pbjs.onEvent === 'function' &&
            window.pbjs.getConfig) {
                console.log("Prebid.js is fully loaded in frame")
                setupPrebidTracking();
        } else {
            if (typeof window.pbjs !== 'undefined') {
                console.log("Prebid.js detected");
            }
            setTimeout(waitForPrebid, 200); // Timeout here
        }
    }

    function setupPrebidTracking() {
        // Track Auction Starts
        pbjs.onEvent('auctionInit', function(data) {
            const auctionTime = performance.now();
            console.log("Auction Started in frame:", frameName, 'ID:', data.auctionId, 'at', auctionTime.toFixed(2), 'ms');
            window.prebidPerformanceData.auctions.push({
                auctionId: data.auctionId,
                startTime: auctionTime,
                timeSincePageLoad: auctionTime - pageLoadTime
            });
        });

        // Track Bid Responses
        pbjs.onEvent('bidResponse', function(bid) {
            const bidTime = performance.now();
            console.log("Bid Response in frame:", frameName, "Bidder:", bid.bidder, "CPM:", bid.cpm, 'at', bidTime.toFixed(2), 'ms');
        });

        // Track Auction End
        pbjs.onEvent('auctionEnd', function(data) {
            const endTime = performance.now();
            console.log("Auction Ended in Frame:", frameName, 'ID:', data.auctionId, 'at', endTime.toFixed(2), 'ms');
        });

        // Track Bid Wins
        pbjs.onEvent('bidWon', function(bid) {
            const winTime = performance.now();
            const timeSincePageLoad = winTime - pageLoadTime;

            console.log('Bid WON on:', frameName);
                console.log('  Bidder:', bid.bidder);
                console.log('  CPM:', bid.cpm);
                console.log('  Ad Unit:', bid.adUnitCode);
                console.log('  Win Time:', winTime.toFixed(2), 'ms');
                console.log('  Time since frame load:', timeSincePageLoad.toFixed(2), 'ms');

            window.prebidPerformanceData.bidWins.push({
                bidder: bid.bidder,
                cpm: bid.cpm,
                adUnitCode: bid.adUnitCode,
                winTime: winTime,
                timeSincePageLoad: timeSincePageLoad,
                auctionId: bid.auctionId
            });
        });

        // Track Ad Rendering
        pbjs.onEvent('adRenderSucceeded', function(data) {
            const renderTime = performance.now();
            const timeSincePageLoad = renderTime - pageLoadTime;

            console.log('AD RENDERED in frame:', frameName);
                console.log('  Ad Unit:', data.adUnitCode);
                console.log('  Render Time:', renderTime.toFixed(2), 'ms');
                console.log('  Time since frame load:', timeSincePageLoad.toFixed(2), 'ms');

            window.prebidPerformanceData.adRenders.push({
                adUnitCode: data.adUnitCode,
                renderTime: renderTime,
                timeSincePageLoad: timeSincePageLoad
            });

            // Calcualte time from bid win to render
            const correspondingWin = window.prebidPerformanceData.bidWins.find(
                win => win.adUnitCode === data.adUnitCode
            );
            if (correspondingWin) {
                const timeToRender = renderTime - correspondingWin.winTime;
                console.log('  Time from bid win to render:', timeToRender.toFixed(2), 'ms');
            }
        });


        // Track Ad Rendering Failures
        pbjs.onEvent('adRenderFailed', function(data) {
            // Logging unit and reasons
            console.log("Ad Render Failed in frame:", frameName);
            console.log('  Ad Unit:', data.adUnitCode);
            console.log('  Reason:', data.reason);
        });

        // Summary Function -> Manual Calling
        window.getPrebidPerformanceSummary = function() {
            const data = window.prebidPerformanceData;
            console.log('Prebid Performance Summary for frame:', frameName);
            console.log('  Frame Load Time:', data.pageLoadTime.toFixed(2), 'ms');
            console.log('  Total Auctions:', data.auctions.length);
            console.log('  Total Bid Wins:', data.bidWins.length);
            console.log('  Total Ad Renders:', data.adRenders.length);

            // Showcase per bid win
            data.bidWins.forEach((win, idx) => {
                console.log(`  Bid Win ${idx + 1}:`);
                console.log(`    Bidder: ${win.bidder}`);
                console.log(`    CPM: ${win.cpm}`);
                console.log(`    Time to win: ${win.timeSincePageLoad.toFixed(2)}ms`);
            
                const render = data.adRenders.find(r => r.adUnitCode === win.adUnitCode);

                if (render) {
                    const timeToRender = render.renderTime - win.winTime;
                    console.log(`    Time to render: ${timeToRender.toFixed(2)}ms`);
                    console.log(`    Total time (load→render): ${render.timeSincePageLoad.toFixed(2)}ms`);
                }
            });

            return data;
        };
    }

    // Start the monitoring
    waitForPrebid();

    window.addEventListener('message', e => {
        if(e.data && e.data.type === "PREBID_SUMMARY") {
            console.log('Prebid Summary Obtained from', e.data.frameName, e.data.payload);
        }
    });

    // Auto-summary after 30 seconds
    setTimeout(() => {
        if (window.getPrebidPerformanceSummary) {
            console.log('\n=== AUTO SUMMARY (30s) for frame', frameName, '===');
            window.getPrebidPerformanceSummary();
            const data = window.getPrebidPerformanceSummary();
            window.parent.postMessage({
                type: "PREBID_SUMMARY",
                frameName,
                payload: data
            }, '*');
        }
    }, 30000);
})();