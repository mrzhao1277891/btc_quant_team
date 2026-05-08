/**
 * SVGVisualizer Unit Tests
 * 
 * Tests the SVGVisualizer class methods to ensure they work correctly.
 */

// Mock DOM environment for testing
class MockSVGElement {
    constructor() {
        this.children = [];
        this.firstChild = null;
    }
    
    appendChild(child) {
        this.children.push(child);
        if (!this.firstChild) {
            this.firstChild = child;
        }
    }
    
    removeChild(child) {
        const index = this.children.indexOf(child);
        if (index > -1) {
            this.children.splice(index, 1);
        }
        if (this.children.length === 0) {
            this.firstChild = null;
        } else {
            this.firstChild = this.children[0];
        }
    }
    
    querySelectorAll(selector) {
        // Simple mock - just return children
        return this.children;
    }
}

class MockSVGGraphicsElement {
    constructor(tagName) {
        this.tagName = tagName;
        this.attributes = {};
        this.textContent = '';
        this.children = [];
    }
    
    setAttribute(name, value) {
        this.attributes[name] = value;
    }
    
    getAttribute(name) {
        return this.attributes[name];
    }
    
    appendChild(child) {
        this.children.push(child);
    }
}

// Mock document.createElementNS
global.document = {
    createElementNS: (ns, tagName) => {
        return new MockSVGGraphicsElement(tagName);
    }
};

// Import the SVGVisualizer class
import { SVGVisualizer } from './SVGVisualizer.js';

// Test Suite
console.log('Running SVGVisualizer Tests...\n');

let passCount = 0;
let failCount = 0;

function test(name, fn) {
    try {
        fn();
        console.log(`✓ PASS: ${name}`);
        passCount++;
    } catch (error) {
        console.log(`✗ FAIL: ${name}`);
        console.log(`  Error: ${error.message}`);
        failCount++;
    }
}

function assert(condition, message) {
    if (!condition) {
        throw new Error(message || 'Assertion failed');
    }
}

function assertEquals(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(message || `Expected ${expected}, got ${actual}`);
    }
}

// Test 1: Constructor
test('Constructor initializes with config', () => {
    const svg = new MockSVGElement();
    const config = {
        width: 800,
        height: 400,
        padding: { top: 20, right: 100, bottom: 20, left: 60 }
    };
    
    const viz = new SVGVisualizer(svg, config);
    
    assert(viz.svgElement === svg, 'SVG element should be stored');
    assertEquals(viz.config.width, 800, 'Width should be 800');
    assertEquals(viz.config.height, 400, 'Height should be 400');
});

// Test 2: drawHorizontalLine creates correct elements
test('drawHorizontalLine creates line and text elements', () => {
    const svg = new MockSVGElement();
    const viz = new SVGVisualizer(svg, {
        width: 800,
        height: 400,
        padding: { top: 20, right: 100, bottom: 20, left: 60 }
    });
    
    viz.drawHorizontalLine(0.5, 'Test Label', '#22c55e', 'solid');
    
    assertEquals(svg.children.length, 1, 'Should have 1 group element');
    
    const group = svg.children[0];
    assertEquals(group.tagName, 'g', 'Should be a group element');
    assertEquals(group.getAttribute('class'), 'horizontal-line', 'Should have correct class');
    assertEquals(group.children.length, 2, 'Group should have 2 children (line and text)');
    
    const line = group.children[0];
    assertEquals(line.tagName, 'line', 'First child should be a line');
    assertEquals(line.getAttribute('stroke'), '#22c55e', 'Line should have correct color');
    assertEquals(line.getAttribute('stroke-width'), '2', 'Line should have width 2');
    
    const text = group.children[1];
    assertEquals(text.tagName, 'text', 'Second child should be text');
    assertEquals(text.textContent, 'Test Label', 'Text should have correct content');
});

// Test 3: drawHorizontalLine with dashed style
test('drawHorizontalLine applies dashed style correctly', () => {
    const svg = new MockSVGElement();
    const viz = new SVGVisualizer(svg, {
        width: 800,
        height: 400,
        padding: { top: 20, right: 100, bottom: 20, left: 60 }
    });
    
    viz.drawHorizontalLine(0.5, 'Dashed Line', '#ef4444', 'dashed');
    
    const group = svg.children[0];
    const line = group.children[0];
    
    assertEquals(line.getAttribute('stroke-dasharray'), '8,4', 'Should have dashed style');
});

// Test 4: drawHorizontalLine with dotted style
test('drawHorizontalLine applies dotted style correctly', () => {
    const svg = new MockSVGElement();
    const viz = new SVGVisualizer(svg, {
        width: 800,
        height: 400,
        padding: { top: 20, right: 100, bottom: 20, left: 60 }
    });
    
    viz.drawHorizontalLine(0.5, 'Dotted Line', '#3b82f6', 'dotted');
    
    const group = svg.children[0];
    const line = group.children[0];
    
    assertEquals(line.getAttribute('stroke-dasharray'), '2,4', 'Should have dotted style');
});

// Test 5: drawMarker with circle shape
test('drawMarker creates circle marker', () => {
    const svg = new MockSVGElement();
    const viz = new SVGVisualizer(svg, {
        width: 800,
        height: 400,
        padding: { top: 20, right: 100, bottom: 20, left: 60 }
    });
    
    viz.drawMarker(0.5, 'Circle Marker', '#22c55e', 'circle');
    
    const group = svg.children[0];
    assertEquals(group.getAttribute('class'), 'marker', 'Should have marker class');
    
    const marker = group.children[0];
    assertEquals(marker.tagName, 'circle', 'Should be a circle element');
    assertEquals(marker.getAttribute('r'), '5', 'Circle should have radius 5');
    assertEquals(marker.getAttribute('fill'), '#22c55e', 'Circle should have correct color');
});

// Test 6: drawMarker with triangle shape
test('drawMarker creates triangle marker', () => {
    const svg = new MockSVGElement();
    const viz = new SVGVisualizer(svg, {
        width: 800,
        height: 400,
        padding: { top: 20, right: 100, bottom: 20, left: 60 }
    });
    
    viz.drawMarker(0.5, 'Triangle Marker', '#f59e0b', 'triangle');
    
    const group = svg.children[0];
    const marker = group.children[0];
    
    assertEquals(marker.tagName, 'polygon', 'Should be a polygon element');
    assert(marker.getAttribute('points'), 'Polygon should have points attribute');
});

// Test 7: drawMarker with square shape
test('drawMarker creates square marker', () => {
    const svg = new MockSVGElement();
    const viz = new SVGVisualizer(svg, {
        width: 800,
        height: 400,
        padding: { top: 20, right: 100, bottom: 20, left: 60 }
    });
    
    viz.drawMarker(0.5, 'Square Marker', '#ef4444', 'square');
    
    const group = svg.children[0];
    const marker = group.children[0];
    
    assertEquals(marker.tagName, 'rect', 'Should be a rect element');
    assertEquals(marker.getAttribute('width'), '10', 'Square should have width 10');
    assertEquals(marker.getAttribute('height'), '10', 'Square should have height 10');
});

// Test 8: drawReferenceLine
test('drawReferenceLine creates dashed reference line', () => {
    const svg = new MockSVGElement();
    const viz = new SVGVisualizer(svg, {
        width: 800,
        height: 400,
        padding: { top: 20, right: 100, bottom: 20, left: 60 }
    });
    
    viz.drawReferenceLine(0.3, 'RSI 70', '#ef4444');
    
    const group = svg.children[0];
    assertEquals(group.getAttribute('class'), 'reference-line', 'Should have reference-line class');
    
    const line = group.children[0];
    assertEquals(line.tagName, 'line', 'Should be a line element');
    assertEquals(line.getAttribute('stroke-dasharray'), '4,4', 'Should be dashed');
    assertEquals(line.getAttribute('opacity'), '0.5', 'Should have 0.5 opacity');
});

// Test 9: drawYAxis
test('drawYAxis creates axis with ticks and labels', () => {
    const svg = new MockSVGElement();
    const viz = new SVGVisualizer(svg, {
        width: 800,
        height: 400,
        padding: { top: 20, right: 100, bottom: 20, left: 60 }
    });
    
    viz.drawYAxis(0, 100, 5);
    
    const group = svg.children[0];
    assertEquals(group.getAttribute('class'), 'y-axis', 'Should have y-axis class');
    
    // Should have 1 axis line + 5 tick lines + 5 text labels = 11 children
    assert(group.children.length >= 10, 'Should have axis line, ticks, and labels');
});

// Test 10: clear method
test('clear removes all SVG elements', () => {
    const svg = new MockSVGElement();
    const viz = new SVGVisualizer(svg, {
        width: 800,
        height: 400,
        padding: { top: 20, right: 100, bottom: 20, left: 60 }
    });
    
    // Add some elements
    viz.drawHorizontalLine(0.3, 'Line 1', '#22c55e', 'solid');
    viz.drawHorizontalLine(0.5, 'Line 2', '#ef4444', 'solid');
    viz.drawMarker(0.7, 'Marker', '#3b82f6', 'circle');
    
    assertEquals(svg.children.length, 3, 'Should have 3 elements before clear');
    
    viz.clear();
    
    assertEquals(svg.children.length, 0, 'Should have 0 elements after clear');
    assertEquals(svg.firstChild, null, 'firstChild should be null after clear');
});

// Test 11: Multiple elements
test('Can draw multiple elements in sequence', () => {
    const svg = new MockSVGElement();
    const viz = new SVGVisualizer(svg, {
        width: 800,
        height: 400,
        padding: { top: 20, right: 100, bottom: 20, left: 60 }
    });
    
    viz.drawYAxis(0, 100, 5);
    viz.drawReferenceLine(0.3, 'RSI 70', '#ef4444');
    viz.drawReferenceLine(0.7, 'RSI 30', '#22c55e');
    viz.drawHorizontalLine(0.4, '1m RSI14: 65.4', '#3b82f6', 'solid');
    viz.drawHorizontalLine(0.5, '1w RSI14: 58.2', '#8a8fa8', 'solid');
    
    assertEquals(svg.children.length, 5, 'Should have 5 elements');
});

// Test 12: Y position normalization
test('Y position is correctly normalized (0-1 range)', () => {
    const svg = new MockSVGElement();
    const viz = new SVGVisualizer(svg, {
        width: 800,
        height: 400,
        padding: { top: 20, right: 100, bottom: 20, left: 60 }
    });
    
    // y=0 should be at top (padding.top)
    viz.drawHorizontalLine(0, 'Top', '#22c55e', 'solid');
    const topGroup = svg.children[0];
    const topLine = topGroup.children[0];
    const topY = parseFloat(topLine.getAttribute('y1'));
    assert(topY === 20, `y=0 should be at top padding (20), got ${topY}`);
    
    // y=1 should be at bottom (height - padding.bottom)
    viz.drawHorizontalLine(1, 'Bottom', '#ef4444', 'solid');
    const bottomGroup = svg.children[1];
    const bottomLine = bottomGroup.children[0];
    const bottomY = parseFloat(bottomLine.getAttribute('y1'));
    assert(bottomY === 380, `y=1 should be at bottom (380), got ${bottomY}`);
});

// Print summary
console.log('\n' + '='.repeat(50));
console.log(`Test Results: ${passCount} passed, ${failCount} failed`);
console.log('='.repeat(50));

if (failCount > 0) {
    process.exit(1);
}
