# 📊 Data Visualization Protocol

## Objective
When a user asks to see a chart, graph, or plot, you MUST use the Vega-Lite JSON specification.
Output the specification inside a markdown code block with the language identifier "vega".

## Critical Rules for React-Vega

1. **Always use Vega-Lite v6:** `"$schema": "https://vega.github.io/schema/vega-lite/v6.json"`
2. **Never use `vconcat` or `hconcat`:** The frontend wrapper uses `width: "container"` and `autosize: "fit"`, which are INCOMPATIBLE with multi-view layouts.
3. **Use Layering instead:** If you need to show multiple data types (e.g., messages and costs), use a `"layer"` array with `"resolve": {"scale": {"y": "independent"}}` to create a dual-axis chart.
4. **Ensure Readability:** ALWAYS add a `"config"` block at the root to increase text size (e.g., `"config": {"axis": {"labelFontSize": 12, "titleFontSize": 14}, "legend": {"labelFontSize": 12, "titleFontSize": 14}}`).

## Example

```vega
{
  "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
  "description": "A simple bar chart with embedded data.",
  "data": {
    "values": [
      {"a": "A", "b": 28}, {"a": "B", "b": 55}, {"a": "C", "b": 43}
    ]
  },
  "mark": "bar",
  "encoding": {
    "x": {"field": "a", "type": "nominal"},
    "y": {"field": "b", "type": "quantitative"}
  }
}
```

Ensure the JSON is perfectly valid. Do not include any other text inside the vega code block.
