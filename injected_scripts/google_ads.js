;(function() {
    window.googleAdsPerformanceData = window.googleAdsPerformanceData || {
        frameName,
        slotResponses: [],
        slotRenders: [],
        impressions: [],
        viewables: []
    }

    // Polling Google Publisher Tags (GPT)
    function waitForGPT() {
        if (window.googletag && Array.isArray(window.googletag.cmd)) {
            window.googletag.cmd.push(initGPTTracking)
        } else {
            setTimeout(waitForGPT, 200)
        }
    }

    // Init
    function initGPTTracking() {
        const pubads = gogoletag.pubads()
        
        
        // Response Back from GPT
        pubads.addEventListener('slotResponseReceived', event => {
            window.googleAdsPerformanceData.slotResponses.push({
                slot: event.slot.getSlotElementId(),
                response: {
                    advertiserId: event.advertiserId,
                    campaignId: event.campaignId,
                    creativeId: event.creativeId,
                    lineItemId: event.lineItemId,
                    isBackfill: event.isBackfill,
                    isEmpty: event.isEmpty
                },
                timestamp: performance.now()
            })
        })

        // iFrame injected
        pubads.addEventListener('slotRenderEnded', event => {
            window.googleAdsPerfromanceData.slotRenders.push({
                slot: event.slot.getSlotElementId(),
                isEmpty: event.isEmpty,
                timestamp: performance.now()
            })
        })

        // Onload 
        pubads.addEventListener('slotOnLoad', event => {
            window.googleAdsPerformanceData.impressions.push({
                slot: event.slot.getSlotElementId(),
                timestamp: performance.now()
            })
        })

        pubads.addEventListener('impressionViewable', event => {
            window.googleAdsPerformanceData.viewables.push({
                slot: event.slot.getSlotElementId(),
                timestamp: performance.now()
            })
        })

        console.log(`[DSQ-GPT] Google Ads Tracking Initialized in frame '${frameName}' `)
    }

        waitForGPT()

        window.getGoogleAdsSummary = () => window.googleAdsPerformanceData
})()