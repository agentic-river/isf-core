# Recharts ResponsiveContainer Best Practices

This guide documents the mandatory rules and solutions for using Recharts in this project, specifically addressing common layout and rendering warnings in React 18+.

## The Problem: The "width(-1) and height(-1)" Warning
When using Recharts `<ResponsiveContainer>` in modern React (React 18+ with concurrent rendering), you will frequently encounter the following warning in the DevTools console:

> `The width(-1) and height(-1) of chart should be greater than 0`

**Root Cause:** `<ResponsiveContainer>` uses a `ResizeObserver` under the hood. On the very first render frame, the DOM has not fully painted or computed its layout, causing Recharts to momentarily receive a width/height of `undefined` or `0` (which it computes to `-1`).

---

## The 3-Step Bulletproof Fix

Whenever you implement a chart using Recharts in this codebase, you MUST follow these three rules to prevent console spam and ensure stable layout rendering:

### 1. Explicit Parent Sizing
Never rely on `flex-grow` or `min-h-[...]` alone for the immediate parent of a `<ResponsiveContainer>`. The parent container MUST have a strictly defined height so the layout engine reserves the exact space before the chart renders.

**❌ BAD:**
```tsx
<div className="flex-grow w-full min-h-[300px]">
  <ResponsiveContainer width="100%" height="100%">
```

**✅ GOOD:**
```tsx
<div className="w-full h-[300px]">
  <ResponsiveContainer width="100%" height="100%">
```

### 2. Provide `initialDimension`
To bridge the split-second gap before the `ResizeObserver` fires, you must provide the `initialDimension` prop to the `<ResponsiveContainer>`. This gives Recharts a valid placeholder to compute against on the very first frame.

**✅ GOOD:**
```tsx
<ResponsiveContainer 
  width="100%" 
  height="100%" 
  initialDimension={{ width: 100, height: 50 }}
>
  <LineChart data={data}>...</LineChart>
</ResponsiveContainer>
```

### 3. Conditional Rendering on Data
Recharts can struggle to calculate dimensions when fed an empty array (`[]`). Prevent the chart from mounting until data is actually available.

**✅ GOOD:**
```tsx
{chartData.length > 0 ? (
  <div className="w-full h-[300px]">
    <ResponsiveContainer 
      width="100%" 
      height="100%" 
      initialDimension={{ width: 100, height: 50 }}
    >
      <LineChart data={chartData}>
         {/* ... */}
      </LineChart>
    </ResponsiveContainer>
  </div>
) : (
  <div className="w-full h-[300px] flex items-center justify-center text-gray-500">
    Loading chart data...
  </div>
)}
```

## Summary Checklist for AI Assistants
When asked to create or fix a Recharts component:
- [ ] Is the immediate parent `div` sized with an explicit height (e.g., `h-[300px]`)?
- [ ] Does the `<ResponsiveContainer>` include `width="100%"`, `height="100%"`, and `initialDimension={{ width: 100, height: 50 }}`?
- [ ] Is the chart conditionally rendered only when `data.length > 0`?
