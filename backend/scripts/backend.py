import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

# This is a mock Python backend script that would process CSV data
# In a real implementation, this would be a Flask or FastAPI service

def load_and_process_csv(file_path):
    """Load and perform initial processing on a CSV file"""
    try:
        df = pd.read_csv(file_path)
        print(f"Successfully loaded {file_path}")
        print(f"Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Basic data cleaning
        df = df.dropna()
        
        return df
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return None

def analyze_data(df, industry, topic, requirement):
    """Perform analysis based on industry, topic and requirement"""
    print(f"Analyzing data for industry: {industry}, topic: {topic}, requirement: {requirement}")
    
    results = {
        "summary": f"Analysis for {industry} industry focusing on {topic} with {requirement} requirements",
        "insights": []
    }
    
    # Example analysis based on topic
    if topic == "sales":
        # Mock sales analysis
        results["insights"].append("Sales have increased by 15% year-over-year")
        results["insights"].append("Product category A shows the highest growth rate")
    elif topic == "customer":
        # Mock customer analysis
        results["insights"].append("Customer retention rate is 78%")
        results["insights"].append("Average customer lifetime value is $1,250")
    
    # Example analysis based on requirement
    if requirement == "trends":
        # Mock trend analysis
        results["trends"] = {
            "upward": ["Product A", "Region B"],
            "downward": ["Product C", "Marketing Channel D"]
        }
    elif requirement == "segmentation":
        # Mock segmentation using K-means
        if df is not None and df.shape[0] > 0:
            # Select numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) > 0:
                # Standardize data
                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(df[numeric_cols])
                
                # Apply PCA for dimensionality reduction
                pca = PCA(n_components=2)
                pca_result = pca.fit_transform(scaled_data)
                
                # Apply K-means clustering
                kmeans = KMeans(n_clusters=4, random_state=42)
                clusters = kmeans.fit_predict(scaled_data)
                
                # Create segment profiles
                results["segments"] = {
                    "count": 4,
                    "sizes": [sum(clusters == i) for i in range(4)],
                    "profiles": [f"Segment {i+1}" for i in range(4)]
                }
    
    return results

def generate_visualizations(df, analysis_results):
    """Generate visualization data for the frontend"""
    print("Generating visualizations")
    
    visualizations = []
    
    if df is not None and df.shape[0] > 0:
        # Example: Bar chart for categorical data
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        if len(categorical_cols) > 0:
            sample_col = categorical_cols[0]
            value_counts = df[sample_col].value_counts().head(5)
            
            visualizations.append({
                "type": "bar",
                "title": f"Distribution of {sample_col}",
                "data": {
                    "labels": value_counts.index.tolist(),
                    "datasets": [{
                        "label": sample_col,
                        "data": value_counts.values.tolist()
                    }]
                }
            })
        
        # Example: Line chart for time series data (FIXED: Updated frequency from 'M' to 'ME')
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(date_cols) > 0 and len(numeric_cols) > 0:
            date_col = date_cols[0]
            numeric_col = numeric_cols[0]
            
            # Convert to datetime if not already
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            
            # Group by month and calculate mean (FIXED: Changed 'M' to 'ME')
            monthly_data = df.groupby(pd.Grouper(key=date_col, freq='ME'))[numeric_col].mean().reset_index()
            
            visualizations.append({
                "type": "line",
                "title": f"{numeric_col} over Time",
                "data": {
                    "labels": monthly_data[date_col].dt.strftime('%Y-%m').tolist(),
                    "datasets": [{
                        "label": numeric_col,
                        "data": monthly_data[numeric_col].tolist()
                    }]
                }
            })
    
    return visualizations

def process_query(query, df, industry, topic):
    """Process a natural language query about the data"""
    print(f"Processing query: {query}")
    
    # In a real implementation, this would use an LLM to interpret the query
    # and generate a response based on the data
    
    response = {
        "answer": f"Based on the analysis of your {industry} data focusing on {topic}, "
    }
    
    # Simple keyword matching for demo purposes
    if "trend" in query.lower():
        response["answer"] += "I've identified an upward trend in the main metrics over the past 6 months."
    elif "compare" in query.lower():
        response["answer"] += "Comparing the segments, Segment A performs 15% better than Segment B."
    elif "predict" in query.lower() or "forecast" in query.lower():
        response["answer"] += "The forecast indicates a 12% growth in the next quarter based on current patterns."
    elif "insight" in query.lower():
        response["answer"] += "A key insight is that customer retention strongly correlates with purchase frequency."
    else:
        response["answer"] += "I've analyzed your data and found several patterns worth investigating further."
    
    return response

# Example usage (this would be called by an API endpoint)
def main():
    # Mock file path - in a real app this would be uploaded by the user
    file_path = "sample_data.csv"
    
    # Create a sample DataFrame for testing
    df = pd.DataFrame({
        'date': pd.date_range(start='2023-01-01', periods=100),
        'sales': np.random.normal(1000, 100, 100),
        'customers': np.random.randint(50, 150, 100),
        'product_category': np.random.choice(['A', 'B', 'C', 'D'], 100),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 100)
    })
    
    # Save sample data
    df.to_csv(file_path, index=False)
    print(f"✅ Created sample data file: {file_path}")
    print(f"📊 Dataset shape: {df.shape}")
    print(f"📋 Columns: {df.columns.tolist()}")
    
    # Process the data
    loaded_df = load_and_process_csv(file_path)
    
    # Analyze based on user selections
    industry = "retail"
    topic = "sales"
    requirement = "trends"
    
    print(f"\n🔍 Running analysis for {industry} industry...")
    analysis_results = analyze_data(loaded_df, industry, topic, requirement)
    
    print(f"\n📈 Generating visualizations...")
    visualizations = generate_visualizations(loaded_df, analysis_results)
    
    # Process a sample query
    query = "What are the trends in my sales data?"
    print(f"\n💬 Processing query: '{query}'")
    query_response = process_query(query, loaded_df, industry, topic)
    
    # Combine results
    final_results = {
        "analysis": analysis_results,
        "visualizations": visualizations,
        "query_response": query_response,
        "data_info": {
            "rows": len(loaded_df),
            "columns": len(loaded_df.columns),
            "file_size": f"{len(df) * len(df.columns) * 8} bytes (estimated)"
        }
    }
    
    # Print results summary
    print(f"\n" + "="*50)
    print("📋 ANALYSIS SUMMARY")
    print("="*50)
    print(f"✅ Analysis Status: Complete")
    print(f"📊 Data Points: {len(loaded_df):,} rows")
    print(f"📈 Visualizations: {len(visualizations)} charts generated")
    print(f"🎯 Industry Focus: {industry}")
    print(f"📋 Topic: {topic}")
    print(f"🔍 Requirement: {requirement}")
    print(f"\n💡 Key Insights:")
    for insight in analysis_results["insights"]:
        print(f"   • {insight}")
    
    print(f"\n🤖 Query Response: {query_response['answer']}")
    print("="*50)
    
    # Print detailed results as JSON (commented out to avoid clutter)
    # print(json.dumps(final_results, indent=2))

if __name__ == "__main__":
    main()
