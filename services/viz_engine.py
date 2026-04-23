import json

class VisualizationEngine:
    @staticmethod
    def detect_chart_type(result, sql):
        """
        Detects the best chart type for the given data.
        """
        if not isinstance(result, list) or len(result) == 0:
            return None
        
        sample = result[0]
        keys = list(sample.keys())
        
        # Heuristics
        sql_lower = sql.lower()
        
        # 1. Time-based (detect date/time columns)
        time_keywords = ['date', 'time', 'year', 'month', 'day', 'created_at', 'updated_at']
        time_col = next((k for k in keys if any(tk in k.lower() for tk in time_keywords)), None)
        
        # 2. Numeric columns for Y-axis
        numeric_cols = [k for k, v in sample.items() if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.','',1).isdigit())]
        
        if time_col and numeric_cols:
            return {
                "chart_type": "line",
                "x_axis": time_col,
                "y_axis": numeric_cols[0],
                "title": "Trend over Time"
            }
        
        # 3. Categorical (if we have a string and a count/sum)
        string_cols = [k for k, v in sample.items() if isinstance(v, str) and k != time_col]
        
        if string_cols and numeric_cols:
            if "count" in sql_lower or "sum" in sql_lower:
                return {
                    "chart_type": "bar",
                    "x_axis": string_cols[0],
                    "y_axis": numeric_cols[0],
                    "title": "Comparison by Category"
                }
        
        # 4. Proportions (Pie chart)
        if len(result) <= 5 and string_cols and numeric_cols:
             return {
                "chart_type": "pie",
                "label": string_cols[0],
                "value": numeric_cols[0],
                "title": "Distribution"
            }
             
        # Fallback to bar if we have at least one string and one number
        if string_cols and numeric_cols:
             return {
                "chart_type": "bar",
                "x_axis": string_cols[0],
                "y_axis": numeric_cols[0],
                "title": "Data Visualization"
            }

        return None
