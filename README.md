# End-to-End Performance Testing Environment for Website and Ad Load Time

A comprehensive testing environment that simulates real-world browser conditions and measures full-page load performance—including ad rendering time—for websites. This tool helps identify performance regressions, optimize loading times, and validate publisher configurations.

## Features

- **Full-page rendering** using headless Chrome via Pyodide
- **Comprehensive performance metrics** including Web Vitals (TTFB, FCP, LCP, DOM completion, load events)
- **Ad performance tracking** with Prebid.js integration
- **Multi-frame support** for iframe-based ad implementations
- **Real-time monitoring** with console logging
- **Screenshot capture** for visual verification
- **CI/CD ready** for automated testing

## Requirements

- Python 3.8+
- Pyodide (`pydoll`)
- Chrome/Chromium browser

## Installation

1. Install dependencies:
```bash
pip install pydoll
```

2. Ensure Chrome/Chromium is installed on your system.

## Usage

### Basic Usage

```bash
python main.py https://example.com
```

### Test Basic Functionality

First, test that Pyodide is working correctly:

```bash
python test.py
```

This will:
- Start a Chrome browser
- Navigate to example.com
- Take a screenshot
- Verify basic functionality

### Monitor Ad Performance

```bash
python main.py https://your-publisher-site.com
```

The script will:
1. Load the specified URL
2. Inject performance tracking scripts
3. Monitor for Prebid.js events
4. Collect performance metrics
5. Wait for user input (press 'q' + Enter to finish)
6. Generate comprehensive reports

## Output

The tool provides several types of output:

### Console Logs
Real-time logging of:
- Page load events
- Prebid.js auction events
- Ad render events
- Performance metrics

### Performance Metrics
- **TTFB (Time to First Byte)**: Server response time
- **FCP (First Contentful Paint)**: First visual content
- **LCP (Largest Contentful Paint)**: Largest content element
- **DOM Content Loaded**: DOM parsing completion
- **Load Event**: Full page load completion

### Ad Performance Data
- Auction start/end times
- Bid responses and wins
- Ad render start/completion
- Time from bid win to render

### Screenshots
- Visual verification of page state
- Saved as `prebid_summary.png`

## JavaScript Files

### `prebid_tracking.js`
Tracks Prebid.js events including:
- Auction initialization
- Bid responses
- Bid wins
- Ad render success/failure
- Performance summaries

### `performance_metrics.js`
Collects comprehensive performance data:
- Navigation timing
- Paint timing
- Resource loading
- Custom performance marks/measures

## Configuration

### Chrome Options
The tool uses several Chrome flags for optimal performance:
- `--disable-blink-features=AutomationControlled`: Avoids detection
- `--disable-web-security`: Allows cross-origin requests
- `--no-sandbox`: Reduces overhead
- `--disable-dev-shm-usage`: Optimizes memory usage

### Customization
You can modify the Chrome options in `main.py`:

```python
options = ChromiumOptions()
options.add_argument("--your-custom-flag")
```

## Troubleshooting

### Common Issues

1. **Chrome not found**: Ensure Chrome/Chromium is installed and in PATH
2. **Permission errors**: Run with appropriate permissions or use `--no-sandbox`
3. **Memory issues**: Reduce timeout values or add memory flags
4. **Network issues**: Check firewall/proxy settings

### Debug Mode

For debugging, you can modify the script to:
- Increase timeout values
- Add more detailed logging
- Disable headless mode (if supported)

## Use Cases

### Publisher Testing
- Validate ad configuration performance
- Identify slow-loading ad networks
- Optimize ad placement and timing

### Performance Regression Testing
- Compare performance across deployments
- Monitor Core Web Vitals
- Track ad load impact on page performance

### A/B Testing
- Compare different ad configurations
- Test optimization strategies
- Validate performance improvements

### CI/CD Integration
- Automated performance testing
- Regression detection
- Performance trend analysis

## Architecture

The tool uses a layered approach:

1. **Browser Layer**: Pyodide Chrome automation
2. **Injection Layer**: JavaScript injection for tracking
3. **Monitoring Layer**: Event collection and logging
4. **Analysis Layer**: Data processing and reporting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review console output for errors
3. Test with the basic test script
4. Open an issue with detailed information
