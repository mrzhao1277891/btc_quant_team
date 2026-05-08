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
     * Draw a horizontal line at y position with label
     * @param {number} y - Y position (0-1 normalized, where 0 is top, 1 is bottom)
     * @param {string} label - Label text to display
     * @param {string} color - Line color (hex or CSS color)
     * @param {string} style - Line style: 'solid' | 'dashed' | 'dotted'
     */
    drawHorizontalLine(y, label, color, style = 'solid') {
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
        line.setAttribute('stroke-width', '2');
        
        // Apply line style
        if (style === 'dashed') {
            line.setAttribute('stroke-dasharray', '8,4');
        } else if (style === 'dotted') {
            line.setAttribute('stroke-dasharray', '2,4');
        }
        
        group.appendChild(line);
        
        // Create label
        const text = document.createElementNS(SVG_NS, 'text');
        text.setAttribute('x', xStart + 10);
        text.setAttribute('y', yPos - 5);
        text.setAttribute('fill', color);
        text.setAttribute('font-size', '12');
        text.setAttribute('font-family', 'monospace');
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
     */
    drawMarker(y, label, color, shape = 'circle') {
        const { padding, width, height } = this.config;
        
        // Convert normalized y to actual SVG coordinates
        const yPos = padding.top + y * (height - padding.top - padding.bottom);
        const xPos = width - padding.right + 10;
        
        // Create group for marker and label
        const group = document.createElementNS(SVG_NS, 'g');
        group.setAttribute('class', 'marker');
        
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
        
        // Create label
        const text = document.createElementNS(SVG_NS, 'text');
        text.setAttribute('x', xPos + 15);
        text.setAttribute('y', yPos + 4);
        text.setAttribute('fill', color);
        text.setAttribute('font-size', '11');
        text.setAttribute('font-family', 'monospace');
        text.textContent = label;
        
        group.appendChild(text);
        
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
        
        // Create dashed line
        const line = document.createElementNS(SVG_NS, 'line');
        line.setAttribute('x1', xStart);
        line.setAttribute('y1', yPos);
        line.setAttribute('x2', xEnd);
        line.setAttribute('y2', yPos);
        line.setAttribute('stroke', color);
        line.setAttribute('stroke-width', '1');
        line.setAttribute('stroke-dasharray', '4,4');
        line.setAttribute('opacity', '0.5');
        
        group.appendChild(line);
        
        // Create label
        const text = document.createElementNS(SVG_NS, 'text');
        text.setAttribute('x', xStart + 10);
        text.setAttribute('y', yPos - 5);
        text.setAttribute('fill', color);
        text.setAttribute('font-size', '10');
        text.setAttribute('font-family', 'monospace');
        text.setAttribute('opacity', '0.7');
        text.textContent = label;
        
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
        axisLine.setAttribute('stroke', '#2a2d3a');
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
            tick.setAttribute('stroke', '#2a2d3a');
            tick.setAttribute('stroke-width', '1');
            
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
