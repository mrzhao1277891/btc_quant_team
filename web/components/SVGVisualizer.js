/**
 * SVGVisualizer.js
 * 
 * Generates SVG elements for horizontal line visualizations.
 * Handles drawing of indicator lines, markers, reference lines, and Y-axis.
 */

const SVG_NS = 'http://www.w3.org/2000/svg';

export class SVGVisualizer {
    constructor(svgElement, config) {
        this.svgElement = svgElement;
        this.config = {
            width: config.width || 800,
            height: config.height || 400,
            padding: config.padding || { top: 20, right: 100, bottom: 20, left: 60 },
            yAxisConfig: config.yAxisConfig || {}
        };
    }

    /**
     * Draw zone separators (vertical lines dividing X-axis into 4 zones)
     */
    drawZoneSeparators() {
        const { padding, width, height } = this.config;
        const yStart = padding.top;
        const yEnd = height - padding.bottom;
        const chartWidth = width - padding.left - padding.right;
        
        // Draw horizontal X-axis line at the bottom
        const xAxisLine = document.createElementNS(SVG_NS, 'line');
        xAxisLine.setAttribute('x1', padding.left);
        xAxisLine.setAttribute('y1', yEnd);
        xAxisLine.setAttribute('x2', width - padding.right);
        xAxisLine.setAttribute('y2', yEnd);
        xAxisLine.setAttribute('stroke', '#6b7280');
        xAxisLine.setAttribute('stroke-width', '2');
        this.svgElement.appendChild(xAxisLine);
        
        // Draw 3 separator lines (at 25%, 50%, 75%)
        [0.25, 0.5, 0.75].forEach(ratio => {
            const xPos = padding.left + chartWidth * ratio;
            
            // Vertical separator line
            const line = document.createElementNS(SVG_NS, 'line');
            line.setAttribute('x1', xPos);
            line.setAttribute('y1', yStart);
            line.setAttribute('x2', xPos);
            line.setAttribute('y2', yEnd);
            line.setAttribute('stroke', '#6b7280');
            line.setAttribute('stroke-width', '1.5');
            line.setAttribute('stroke-dasharray', '4,4');
            line.setAttribute('opacity', '0.6');
            this.svgElement.appendChild(line);
            
            // Tick mark on X-axis
            const tick = document.createElementNS(SVG_NS, 'line');
            tick.setAttribute('x1', xPos);
            tick.setAttribute('y1', yEnd);
            tick.setAttribute('x2', xPos);
            tick.setAttribute('y2', yEnd + 5);
            tick.setAttribute('stroke', '#6b7280');
            tick.setAttribute('stroke-width', '2');
            this.svgElement.appendChild(tick);
        });
        
        // Draw tick marks at zone boundaries (0%, 25%, 50%, 75%, 100%)
        [0, 0.25, 0.5, 0.75, 1.0].forEach(ratio => {
            const xPos = padding.left + chartWidth * ratio;
            
            const tick = document.createElementNS(SVG_NS, 'line');
            tick.setAttribute('x1', xPos);
            tick.setAttribute('y1', yEnd);
            tick.setAttribute('x2', xPos);
            tick.setAttribute('y2', yEnd + 5);
            tick.setAttribute('stroke', '#6b7280');
            tick.setAttribute('stroke-width', '2');
            this.svgElement.appendChild(tick);
        });
    }

    /**
     * Draw zone labels at the bottom of the chart
     * @param {Array} zones - Array of zone objects with label, xStart, xEnd
     */
    drawZoneLabels(zones) {
        const { padding, width, height } = this.config;
        const yPos = height - padding.bottom + 20;
        const chartWidth = width - padding.left - padding.right;
        
        zones.forEach(zone => {
            const xCenter = padding.left + chartWidth * (zone.xStart + zone.xEnd) / 2;
            
            const text = document.createElementNS(SVG_NS, 'text');
            text.setAttribute('x', xCenter);
            text.setAttribute('y', yPos);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('fill', '#8a8fa8');
            text.setAttribute('font-size', '13');
            text.setAttribute('font-family', 'monospace');
            text.setAttribute('font-weight', 'bold');
            text.textContent = zone.label;
            
            this.svgElement.appendChild(text);
        });
    }

    /**
     * Draw a data point (circle) with hover tooltip
     * @param {number} x - X position (0-1 normalized)
     * @param {number} y - Y position (0-1 normalized)
     * @param {number} size - Dot size (radius in pixels)
     * @param {string} color - Dot color
     * @param {Object} tooltip - Tooltip data {timeframe, indicator, value}
     */
    drawDataPoint(x, y, size, color, tooltip) {
        const { padding, width, height } = this.config;
        
        // Convert normalized positions to actual SVG coordinates
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;
        const xPos = padding.left + x * chartWidth;
        const yPos = padding.top + y * chartHeight;
        
        // Create group for dot and tooltip
        const group = document.createElementNS(SVG_NS, 'g');
        group.setAttribute('class', 'data-point');
        
        // Create circle
        const circle = document.createElementNS(SVG_NS, 'circle');
        circle.setAttribute('cx', xPos);
        circle.setAttribute('cy', yPos);
        circle.setAttribute('r', size);
        circle.setAttribute('fill', color);
        circle.setAttribute('opacity', '0.8');
        circle.setAttribute('cursor', 'pointer');
        circle.setAttribute('pointer-events', 'none'); // Let the hover area handle events
        
        // Create larger invisible hover area for easier interaction
        const hoverArea = document.createElementNS(SVG_NS, 'circle');
        hoverArea.setAttribute('cx', xPos);
        hoverArea.setAttribute('cy', yPos);
        hoverArea.setAttribute('r', Math.max(size * 2, 12)); // At least 12px radius for easy hovering
        hoverArea.setAttribute('fill', 'transparent');
        hoverArea.setAttribute('cursor', 'pointer');
        hoverArea.setAttribute('class', 'hover-area');
        
        // Create tooltip text (hidden by default)
        const tooltipText = document.createElementNS(SVG_NS, 'text');
        tooltipText.setAttribute('x', xPos);
        tooltipText.setAttribute('y', yPos - size - 12); // Move up a bit more
        tooltipText.setAttribute('text-anchor', 'middle');
        tooltipText.setAttribute('fill', '#ffffff'); // White text for better contrast
        tooltipText.setAttribute('font-size', '11');
        tooltipText.setAttribute('font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif');
        tooltipText.setAttribute('font-weight', '600');
        tooltipText.setAttribute('opacity', '0');
        tooltipText.setAttribute('class', 'tooltip-text');
        tooltipText.setAttribute('pointer-events', 'none'); // Don't interfere with hover
        tooltipText.style.transition = 'opacity 0.2s ease';
        
        // Build tooltip text with optional extra info
        let tooltipContent = `${tooltip.timeframe} ${tooltip.indicator}: ${tooltip.value}`;
        if (tooltip.extra) {
            tooltipContent += ` (${tooltip.extra})`;
        }
        tooltipText.textContent = tooltipContent;
        
        // Create tooltip background
        const tooltipBg = document.createElementNS(SVG_NS, 'rect');
        tooltipBg.setAttribute('fill', '#1a1d2e');
        tooltipBg.setAttribute('stroke', color);
        tooltipBg.setAttribute('stroke-width', '1');
        tooltipBg.setAttribute('opacity', '0');
        tooltipBg.setAttribute('rx', '4');
        tooltipBg.setAttribute('class', 'tooltip-bg');
        tooltipBg.setAttribute('pointer-events', 'none'); // Don't interfere with hover
        tooltipBg.style.transition = 'opacity 0.2s ease';
        
        // Add hover events to the hover area
        hoverArea.addEventListener('mouseenter', () => {
            circle.setAttribute('r', size * 1.5);
            circle.setAttribute('opacity', '1');
            tooltipText.setAttribute('opacity', '1');
            tooltipBg.setAttribute('opacity', '0.95');
            
            // Calculate tooltip background size with padding
            const bbox = tooltipText.getBBox();
            tooltipBg.setAttribute('x', bbox.x - 6);
            tooltipBg.setAttribute('y', bbox.y - 3);
            tooltipBg.setAttribute('width', bbox.width + 12);
            tooltipBg.setAttribute('height', bbox.height + 6);
        });
        
        hoverArea.addEventListener('mouseleave', () => {
            circle.setAttribute('r', size);
            circle.setAttribute('opacity', '0.8');
            tooltipText.setAttribute('opacity', '0');
            tooltipBg.setAttribute('opacity', '0');
        });
        
        group.appendChild(tooltipBg);
        group.appendChild(circle);
        group.appendChild(hoverArea); // Add hover area on top
        group.appendChild(tooltipText);
        
        this.svgElement.appendChild(group);
    }

    /**
     * Draw a horizontal line at y position with label
     * @param {number} y - Y position (0-1 normalized, where 0 is top, 1 is bottom)
     * @param {string} label - Label text to display
     * @param {string} color - Line color (hex or CSS color)
     * @param {string} style - Line style: 'solid' | 'dashed' | 'dotted'
     * @param {number} weight - Line weight/thickness (default: 2)
     * @param {number} opacity - Line opacity 0-1 (default: 1)
     * @param {number} fontSize - Label font size (default: 12)
     */
    drawHorizontalLine(y, label, color, style = 'solid', weight = 2, opacity = 1, fontSize = 12) {
        const { padding, width, height } = this.config;
        
        // Convert normalized y (0-1) to actual SVG coordinates
        const yPos = padding.top + y * (height - padding.top - padding.bottom);
        const xStart = padding.left;
        const xEnd = width - padding.right;
        
        // Create group for line and label
        const group = document.createElementNS(SVG_NS, 'g');
        group.setAttribute('class', 'horizontal-line');
        
        // Create line
        const line = document.createElementNS(SVG_NS, 'line');
        line.setAttribute('x1', xStart);
        line.setAttribute('y1', yPos);
        line.setAttribute('x2', xEnd);
        line.setAttribute('y2', yPos);
        line.setAttribute('stroke', color);
        line.setAttribute('stroke-width', weight.toString());
        line.setAttribute('opacity', opacity.toString());
        
        // Apply line style
        if (style === 'dashed') {
            line.setAttribute('stroke-dasharray', '8,4');
        } else if (style === 'dotted') {
            line.setAttribute('stroke-dasharray', '2,4');
        }
        
        group.appendChild(line);
        
        // Create label with smart positioning to avoid overlap
        const text = document.createElementNS(SVG_NS, 'text');
        text.setAttribute('x', xStart + 10);
        text.setAttribute('y', yPos - 5);
        text.setAttribute('fill', color);
        text.setAttribute('font-size', fontSize.toString());
        text.setAttribute('font-family', 'monospace');
        text.setAttribute('font-weight', weight > 2.5 ? 'bold' : 'normal');
        text.setAttribute('opacity', opacity.toString());
        text.textContent = label;
        
        group.appendChild(text);
        
        this.svgElement.appendChild(group);
    }

    /**
     * Draw a marker (circle, triangle, square) at y position
     * @param {number} y - Y position (0-1 normalized)
     * @param {string} label - Label text to display
     * @param {string} color - Marker color
     * @param {string} shape - Marker shape: 'circle' | 'triangle' | 'square'
     * @param {number} opacity - Marker opacity 0-1 (default: 1)
     */
    drawMarker(y, label, color, shape = 'circle', opacity = 1) {
        const { padding, width, height } = this.config;
        
        // Convert normalized y to actual SVG coordinates
        const yPos = padding.top + y * (height - padding.top - padding.bottom);
        const xPos = width - padding.right + 10;
        
        // Create group for marker and label
        const group = document.createElementNS(SVG_NS, 'g');
        group.setAttribute('class', 'marker');
        group.setAttribute('opacity', opacity.toString());
        
        // Create marker shape
        let marker;
        if (shape === 'circle') {
            marker = document.createElementNS(SVG_NS, 'circle');
            marker.setAttribute('cx', xPos);
            marker.setAttribute('cy', yPos);
            marker.setAttribute('r', '5');
            marker.setAttribute('fill', color);
        } else if (shape === 'triangle') {
            marker = document.createElementNS(SVG_NS, 'polygon');
            const points = `${xPos},${yPos - 6} ${xPos - 5},${yPos + 4} ${xPos + 5},${yPos + 4}`;
            marker.setAttribute('points', points);
            marker.setAttribute('fill', color);
        } else if (shape === 'square') {
            marker = document.createElementNS(SVG_NS, 'rect');
            marker.setAttribute('x', xPos - 5);
            marker.setAttribute('y', yPos - 5);
            marker.setAttribute('width', '10');
            marker.setAttribute('height', '10');
            marker.setAttribute('fill', color);
        }
        
        group.appendChild(marker);
        
        // Create label if provided
        if (label) {
            const text = document.createElementNS(SVG_NS, 'text');
            text.setAttribute('x', xPos + 15);
            text.setAttribute('y', yPos + 4);
            text.setAttribute('fill', color);
            text.setAttribute('font-size', '11');
            text.setAttribute('font-family', 'monospace');
            text.textContent = label;
            
            group.appendChild(text);
        }
        
        this.svgElement.appendChild(group);
    }

    /**
     * Draw a reference line (e.g., RSI 30/70, MACD 0)
     * @param {number} y - Y position (0-1 normalized)
     * @param {string} label - Label text to display
     * @param {string} color - Line color
     */
    drawReferenceLine(y, label, color) {
        const { padding, width, height } = this.config;
        
        // Convert normalized y to actual SVG coordinates
        const yPos = padding.top + y * (height - padding.top - padding.bottom);
        const xStart = padding.left;
        const xEnd = width - padding.right;
        
        // Create group for reference line
        const group = document.createElementNS(SVG_NS, 'g');
        group.setAttribute('class', 'reference-line');
        
        // Create dashed line (darker and more visible)
        const line = document.createElementNS(SVG_NS, 'line');
        line.setAttribute('x1', xStart);
        line.setAttribute('y1', yPos);
        line.setAttribute('x2', xEnd);
        line.setAttribute('y2', yPos);
        line.setAttribute('stroke', '#9ca3af');  // Darker gray for better visibility
        line.setAttribute('stroke-width', '2');
        line.setAttribute('stroke-dasharray', '6,3');
        line.setAttribute('opacity', '0.8');
        
        group.appendChild(line);
        
        // Create label (darker and more visible)
        const text = document.createElementNS(SVG_NS, 'text');
        text.setAttribute('x', xStart + 10);
        text.setAttribute('y', yPos - 5);
        text.setAttribute('fill', '#9ca3af');
        text.setAttribute('font-size', '11');
        text.setAttribute('font-family', 'monospace');
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('opacity', '0.9');
        text.textContent = label;
        
        group.appendChild(text);
        
        this.svgElement.appendChild(group);
    }

    /**
     * Draw current price reference line (horizontal dashed line)
     * @param {number} y - Y position (0-1 normalized)
     * @param {string} label - Label text to display
     * @param {string} color - Line color
     */
    drawPriceReferenceLine(y, label, color) {
        const { padding, width, height } = this.config;
        
        // Convert normalized y to actual SVG coordinates
        const yPos = padding.top + y * (height - padding.top - padding.bottom);
        const xStart = padding.left;
        const xEnd = width - padding.right;
        
        // Create group for price reference line
        const group = document.createElementNS(SVG_NS, 'g');
        group.setAttribute('class', 'price-reference-line');
        
        // Create dashed line (more prominent than regular reference lines)
        const line = document.createElementNS(SVG_NS, 'line');
        line.setAttribute('x1', xStart);
        line.setAttribute('y1', yPos);
        line.setAttribute('x2', xEnd);
        line.setAttribute('y2', yPos);
        line.setAttribute('stroke', color);
        line.setAttribute('stroke-width', '2');
        line.setAttribute('stroke-dasharray', '8,4');
        line.setAttribute('opacity', '0.7');
        
        group.appendChild(line);
        
        // Extract just the price value from label (remove "当前价格: " prefix)
        const priceValue = label.replace('当前价格: ', '');
        
        // Create background rectangle for price label (on the right side)
        const bgRect = document.createElementNS(SVG_NS, 'rect');
        bgRect.setAttribute('x', xEnd + 5);
        bgRect.setAttribute('y', yPos - 10);
        bgRect.setAttribute('width', '90');
        bgRect.setAttribute('height', '20');
        bgRect.setAttribute('fill', color);
        bgRect.setAttribute('opacity', '0.9');
        bgRect.setAttribute('rx', '3');
        
        group.appendChild(bgRect);
        
        // Create price label on the right side of Y-axis
        const text = document.createElementNS(SVG_NS, 'text');
        text.setAttribute('x', xEnd + 50);
        text.setAttribute('y', yPos + 4);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', '#ffffff');
        text.setAttribute('font-size', '12');
        text.setAttribute('font-family', 'monospace');
        text.setAttribute('font-weight', 'bold');
        text.textContent = priceValue;
        
        group.appendChild(text);
        
        this.svgElement.appendChild(group);
    }

    /**
     * Draw Y-axis with tick marks and labels
     * @param {number} min - Minimum value
     * @param {number} max - Maximum value
     * @param {number} ticks - Number of tick marks
     */
    drawYAxis(min, max, ticks = 5) {
        const { padding, height } = this.config;
        const xPos = padding.left;
        const yStart = padding.top;
        const yEnd = height - padding.bottom;
        
        // Create group for Y-axis
        const group = document.createElementNS(SVG_NS, 'g');
        group.setAttribute('class', 'y-axis');
        
        // Draw main axis line
        const axisLine = document.createElementNS(SVG_NS, 'line');
        axisLine.setAttribute('x1', xPos);
        axisLine.setAttribute('y1', yStart);
        axisLine.setAttribute('x2', xPos);
        axisLine.setAttribute('y2', yEnd);
        axisLine.setAttribute('stroke', '#6b7280');
        axisLine.setAttribute('stroke-width', '2');
        
        group.appendChild(axisLine);
        
        // Draw tick marks and labels
        const range = max - min;
        const step = range / (ticks - 1);
        
        for (let i = 0; i < ticks; i++) {
            const value = max - (i * step); // Start from max at top
            const yPos = yStart + (i * (yEnd - yStart) / (ticks - 1));
            
            // Draw tick mark
            const tick = document.createElementNS(SVG_NS, 'line');
            tick.setAttribute('x1', xPos - 5);
            tick.setAttribute('y1', yPos);
            tick.setAttribute('x2', xPos);
            tick.setAttribute('y2', yPos);
            tick.setAttribute('stroke', '#6b7280');
            tick.setAttribute('stroke-width', '1.5');
            
            group.appendChild(tick);
            
            // Draw label
            const text = document.createElementNS(SVG_NS, 'text');
            text.setAttribute('x', xPos - 10);
            text.setAttribute('y', yPos + 4);
            text.setAttribute('text-anchor', 'end');
            text.setAttribute('fill', '#8a8fa8');
            text.setAttribute('font-size', '11');
            text.setAttribute('font-family', 'monospace');
            
            // Format value based on range
            let formattedValue;
            if (range > 1000) {
                formattedValue = Math.round(value).toLocaleString();
            } else if (range > 10) {
                formattedValue = value.toFixed(1);
            } else {
                formattedValue = value.toFixed(2);
            }
            
            text.textContent = formattedValue;
            
            group.appendChild(text);
        }
        
        this.svgElement.appendChild(group);
    }

    /**
     * Clear all SVG elements
     */
    clear() {
        if (this.svgElement) {
            // Remove all child elements
            while (this.svgElement.firstChild) {
                this.svgElement.removeChild(this.svgElement.firstChild);
            }
        }
    }
}

export default SVGVisualizer;
