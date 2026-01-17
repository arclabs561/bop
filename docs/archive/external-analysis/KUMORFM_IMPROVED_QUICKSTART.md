# KumoRFM Quickstart

[Blog | Paper]

KumoRFM (Kumo Relational Foundation Model) is a Foundation Model for machine learning on enterprise data. With just your data and a few lines of code, you can generate accurate predictions in real-time: no model training or pipelines required.

---

## What You'll Build

By the end of this tutorial, you'll be able to:

✅ **Predict customer behavior**: "Will user 42 place orders in the next 30 days?"
✅ **Forecast product demand**: "How much revenue will item 42 generate next month?"
✅ **Recommend products**: "What are the top 10 items user 123 is likely to buy?"
✅ **Infer missing data**: "What's the age of user 8 if it's missing?"

**Example output**:
```
ENTITY          ANCHOR_TIMESTAMP  TARGET_PRED  True_PROB
users.user_id=42  2024-09-19       False        0.73
```

**Time to value**: ~15 minutes from installation to first prediction.

---

## Learning Objectives

By completing this tutorial, you will be able to:

1. **Create relational graphs** from pandas DataFrames
   - **Evidence**: Build a 3-table graph with proper linking
   - **Benefit**: Understand how to structure your data for predictions
   
2. **Write predictive queries** using PQL syntax
   - **Evidence**: Write queries for forecasting, churn, and recommendations
   - **Benefit**: Solve real business problems with simple queries
   
3. **Interpret prediction results** and make business decisions
   - **Evidence**: Explain what each column means and when to act on predictions
   - **Benefit**: Turn predictions into actionable insights
   
4. **Troubleshoot common issues** in graph creation
   - **Evidence**: Identify and fix primary key, time column, and semantic type errors
   - **Benefit**: Debug problems independently

**Time to mastery**: ~15 minutes for basics, ~1 hour for proficiency

---

## Choose Your Path

**New to machine learning?**
→ Start with [Understanding the Concepts](#introduction) (5 min)
→ Then follow [Full Tutorial](#full-tutorial) step-by-step

**Familiar with ML but new to KumoRFM?**
→ Skip to [Quick Start](#quick-start-30-seconds) (30 sec)
→ Then jump to [Writing Predictive Queries](#step-7-write-a-predictive-query) (10 min)

**Expert user?**
→ [Quick Start](#quick-start-30-seconds) for immediate value
→ [API Reference](#api-reference) for complete syntax (coming soon)
→ [Advanced Patterns](#advanced-patterns) for optimization (coming soon)
→ [Troubleshooting Guide](#troubleshooting) for edge cases (coming soon)

---

## Quick Start (30 seconds)

See KumoRFM in action with minimal setup:

```python
import kumoai.experimental.rfm as rfm
import pandas as pd

# Authenticate (one-time setup)
rfm.authenticate()

# Load sample data
root = 's3://kumo-sdk-public/rfm-datasets/online-shopping'
users_df = pd.read_parquet(f'{root}/users.parquet')
orders_df = pd.read_parquet(f'{root}/orders.parquet')

# Create graph and predict
graph = rfm.LocalGraph.from_data(
    {'users': users_df, 'orders': orders_df}, 
    infer_metadata=True
)
model = rfm.KumoRFM(graph)
result = model.predict("PREDICT COUNT(orders.*, 0, 30, days) FOR users.user_id=42")
print(result)
```

**What this does**: Predicts how many orders user 42 will place in the next 30 days.

**Next**: Follow the [Full Tutorial](#full-tutorial) below to understand each step in detail.

---

## Introduction

KumoRFM is grounded in three key world views:

### 1. Enterprise data is a graph.

Enterprise data is a graph where tables are connected by keys.

Below is an example database where ITEMS table and ORDERS table are linked by item_id.

Once we structure enterprise data as a graph, we can apply pre-trained Relational Graph Transformers to extract insights and patterns.

### 2. With timestamps, we place events on a timeline.

By placing events on a timeline, we unlock the ability to model how things evolve over time. This makes it possible to select any point in time and predict what is likely to happen next, based on the sequence and patterns in historical data.

### 3. Machine learning tasks can be described via predictive queries.

All major machine learning tasks—regression, classification, recommendation—can be defined using a Predictive Query language (PQL).

If you know SQL, picking up PQL is a breeze. It will feel familiar right away. Learn more about PQL here.

---

## Full Tutorial

Let's get started with the complete step-by-step guide!

### Step 1. Install the Kumo Python SDK

KumoRFM provides an SDK in Python. The Kumo SDK is available for Python 3.9 to Python 3.13.

```python
!pip install kumoai
```

```python
import kumoai.experimental.rfm as rfm
```

**Note**: The API of `kumoai.experimental.rfm` may change in the near future.

**Why this step matters**: The SDK provides the interface to KumoRFM's prediction engine. Without it, you can't create graphs or make predictions.

---

### Step 2. Get an API key

You will need an API key to make calls to KumoRFM. Use the widget below to generate one for free by clicking "Generate API Key". If you don't have a KumoRFM account, the widget will prompt you to signup.

You will see the following when your key has been created successfully:

```python
import os
if not os.environ.get("KUMO_API_KEY"):
    rfm.authenticate()
```

**Why this step matters**: The API key authenticates your requests to KumoRFM's cloud service, enabling predictions without running models locally.

---

### Step 3. Initialize a client

If you completed step 2 via the widget, you don't need to change anything. `KUMO_API_KEY` is already set as environment variable.

If you bring the API key from the website, you can manually change the `KUMO_API_KEY` below:

```python
# Initialize a Kumo client with your API key:
KUMO_API_KEY = os.environ.get("KUMO_API_KEY")
rfm.init(api_key=KUMO_API_KEY)
```

**Why this step matters**: Initialization configures the SDK to communicate with KumoRFM's servers using your credentials.

---

### Step 4. Import your data

KumoRFM interacts with a set of `pd.DataFrame` objects:

```python
import pandas as pd

root = 's3://kumo-sdk-public/rfm-datasets/online-shopping'
users_df = pd.read_parquet(f'{root}/users.parquet')
items_df = pd.read_parquet(f'{root}/items.parquet')
orders_df = pd.read_parquet(f'{root}/orders.parquet')

# NOTE You can use `pd.read_csv(...)` to read CSV files instead.
# You don't need to use s3 to import your data.
# For Colab users, you can upload your data to the file folder (the folder icon on the left panel), and directly import from there.
# You can also download this notebook, and import your data locally.
```

We can inspect the data and its types in-memory:

```python
# Inspect a `pandas.DataFrame`:
users_df.head(3)
```

```python
# Inspect the data types of a `pandas.DataFrame`:
users_df.dtypes
```

```python
# Optional: Change the data type of columns (if necessary):
users_df['user_id'] = users_df['user_id'].astype(int)
```

**Why this step matters**: Your data must be in pandas DataFrames for KumoRFM to process. This step ensures your data is loaded and ready for table creation.

---

### Step 5. Create KumoRFM Tables

A `LocalTable` acts as a lightweight abstraction of a `pandas.DataFrame`, providing additional integration.

A `LocalTable` tells KumoRFM three things about your data. We'll cover each separately:

#### Step 5a: Set Primary Keys

**What it is**: A column that uniquely identifies each row (like `user_id` in the users table).

**Why it matters**: KumoRFM uses primary keys to:
1. Link tables together (when creating a graph)
2. Identify which entities to generate predictions for

**Example**:
```python
users = rfm.LocalTable(users_df, name="users")
users.primary_key = "user_id"  # This row uniquely identifies each user
```

#### How Primary Keys Enable Graph Linking

**Concept**: Primary keys create unique identifiers that allow KumoRFM to connect related data across tables.

**Why this matters**: When you set `user_id` as the primary key in the `users` table, KumoRFM can:
1. Link orders to users by matching `orders.user_id` to `users.user_id`
2. Track which user each order belongs to
3. Aggregate order patterns per user for predictions

**Mental model**: Think of primary keys as unique addresses. Just like a mailing address uniquely identifies a house, a primary key uniquely identifies each row. Foreign keys in other tables "point to" these addresses to create relationships.

#### Try It Now

```python
# Your turn: Set the primary key for the items table
items = rfm.LocalTable(items_df, name="items")
# TODO: Set the primary key here
# Hint: Look at the column names in items_df.head()

# Check your answer (uncomment to verify):
# assert items.primary_key == "item_id", "Try again! The primary key should be 'item_id'"
# print("✅ Correct! You've set the primary key.")
```

<details>
<summary>Show solution</summary>

```python
items = rfm.LocalTable(items_df, name="items")
items.primary_key = "item_id"  # item_id uniquely identifies each item
```

</details>

---

#### Step 5b: Add Time Columns (Optional but Recommended)

**What it is**: A timestamp column showing when events occurred (like `date` in the orders table).

**Why it matters**: Enables temporal predictions—KumoRFM can model how patterns change over time. Without a time column, you can only make static predictions, not forecast future events.

**Example**:
```python
orders = rfm.LocalTable(orders_df, name="orders")
orders.time_column = "date"  # When did this order happen?
```

#### How Time Columns Enable Temporal Predictions

**Concept**: Time columns allow KumoRFM to understand the sequence of events and model how patterns change over time.

**Why this matters**: With a time column, KumoRFM can:
1. Order events chronologically (see which orders came first)
2. Identify trends (order frequency increasing or decreasing)
3. Model temporal patterns (seasonal buying, user lifecycle stages)
4. Make future predictions based on historical sequences

**Mental model**: Think of time columns as creating a timeline. Each event gets a position on this timeline. KumoRFM uses this timeline to learn patterns like "users who order in January often order again in March" or "new users place orders more frequently in their first month."

**When to use**: If you want to predict future events based on historical patterns (which is most use cases).

#### Try It Now

```python
# Your turn: Set the time column for the orders table
orders = rfm.LocalTable(orders_df, name="orders")
# TODO: Set the time column here
# Hint: Look for a column with dates or timestamps

# Check your answer (uncomment to verify):
# assert orders.time_column == "date", "Try again! The time column should be 'date'"
# print("✅ Correct! You've set the time column.")
```

<details>
<summary>Show solution</summary>

```python
orders = rfm.LocalTable(orders_df, name="orders")
orders.time_column = "date"  # date column contains timestamps
```

</details>

---

#### Step 5c: Set Semantic Types (Advanced)

**What it is**: Tells KumoRFM how to interpret each column (numerical, categorical, text, etc.).

**Why it matters**: Affects how KumoRFM encodes data for machine learning. Correct types improve prediction accuracy. For instance, if you want to perform missing value imputation, the semantic type will determine whether it is treated as a regression task (`stype="numerical"`) or a classification task (`stype="categorical"`).

**Quick setup**: Use automatic inference (works for most cases):
```python
users = rfm.LocalTable(users_df, name="users").infer_metadata()
orders = rfm.LocalTable(orders_df, name="orders").infer_metadata()
items = rfm.LocalTable(items_df, name="items").infer_metadata()
```

**Manual control**: If you prefer more explicit control, you can manually assign metadata:

```python
orders = rfm.LocalTable(
    orders_df,
    name="orders",
    primary_key="order_id",
    time_column="date"
)
```

You can inspect the metadata of the table:

```python
users.print_metadata()
```

... and apply any required changes manually:

```python
# Update the semantic type (stype) of columns:
users['user_id'].stype = "ID"
users['age'].stype = "numerical"

# Set primary key:
users.primary_key = "user_id"

# Set time column:
orders.time_column = "date"
```

**Semantic Types Reference** (click to expand):

<details>
<summary>Complete Semantic Types Reference</summary>

| Type | Explanation | Example |
|------|-------------|---------|
| `"numerical"` | Numerical values (e.g., price, age) | 25, 3.14, -10 |
| `"categorical"` | Discrete categories with limited cardinality | Color: "red", "blue", "green" (one cell may only have one category) |
| `"multicategorical"` | Multiple categories in a single cell | "Action\|Drama\|Comedy", "Action\|Thriller" |
| `"ID"` | An identifier, e.g., primary keys or foreign keys | user_id: 123, product_id: PRD-8729453 |
| `"text"` | Natural language text | Descriptions |
| `"timestamp"` | Specific point in time | "2025-07-11", "2023-02-12 09:47:58" |
| `"sequence"` | Custom embeddings or sequential data | [0.25, -0.75, 0.50, ...] |

**Primary Key Notes**:
- The primary key is a unique identifier of each row in a table.
- If there are duplicated primary keys, the system will only keep the first one.
- A primary key can be used to link tables through primary key--foreign key relationship.
- In the users table: `user_id` is the primary key.
- In the orders table: `order_id` is the primary key, and `user_id` is a foreign key that points back to the users table.
- A primary key does not need to link to other tables. For example, in the orders table, the primary key (`order_id`) is not used for linking, but it still serves its main purpose—to uniquely identify each row in the table.
- `primary_key` can only be assigned to columns holding integers, floating point values or strings.
- Each table can have at most one `primary_key` column.

**Time Column Notes**:
- Indicates the timestamp column that record when the event occurred.
- Time column data must be able to be parsed via `pandas.to_datetime`.
- Each table can have at most one `time_column` column.

</details>

---

### Step 6. Create a graph in two simple steps

We are now ready to inter-connect our tables to form a `LocalGraph`. But how to get started with building a graph? What tables should you include?

**A good guiding principle is to start simple**: begin with just the minimal set of tables needed to support the prediction task you care about. Focus on the core entities and relationships essential to prediction.

For example, suppose your goal is to predict a user's future orders. At a minimum, your graph only needs two tables:
- `users`: representing each user
- `orders`: representing the orders placed by those users

This minimal setup forms a usable graph for prediction. From there, you can gradually add complexity. For instance, you might later introduce an `items` table, so that RFM can take into account item information.

#### Visualizing the Graph Structure

Before we link tables, let's visualize the relationships:

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   users     │         │   orders    │         │   items     │
├─────────────┤         ├─────────────┤         ├─────────────┤
│ user_id (PK)│◄────────│ user_id (FK)│         │ item_id (PK)│
│ age         │         │ order_id(PK)│         │ name        │
│ location    │         │ item_id (FK)│────────►│ category    │
└─────────────┘         │ date        │         │ price       │
                         │ price       │         └─────────────┘
                         └─────────────┘
```

**Diagram description** (for screen readers): Three tables connected in a graph structure. The users table (left) contains user_id as primary key, age, and location. The orders table (center) contains user_id as foreign key pointing to users, order_id as primary key, item_id as foreign key pointing to items, date, and price. The items table (right) contains item_id as primary key, name, category, and price. Arrows show relationships: orders.user_id links to users.user_id, and orders.item_id links to items.item_id.

**Key**: PK = Primary Key, FK = Foreign Key

The `orders` table connects to both `users` and `items` through foreign keys. This creates a graph where:
- Each user can have multiple orders (one-to-many)
- Each order links to one item (many-to-one)
- KumoRFM can traverse these relationships to make predictions

#### How Graphs Enable Predictions

**Concept**: KumoRFM uses graph structure to traverse relationships and discover patterns across connected data.

**Why this matters**: When you link `orders` to `users`, KumoRFM can:
1. **See behavioral patterns**: Which users place frequent orders, what times they order, how order frequency changes
2. **Identify collaborative patterns**: Items popular with similar users (collaborative filtering)
3. **Model temporal patterns**: How order frequency changes over time for different user segments
4. **Leverage cross-table features**: User demographics + order history + item properties = richer predictions

**Mental model**: Think of the graph as a knowledge network. Each table is a node (like a city), each link is a relationship (like a road). KumoRFM "walks" this network to find patterns:
- It might discover: "Users in location X who ordered item Y in the past 30 days are likely to order item Z"
- This pattern emerges from traversing: users → orders → items → back to users

**Without graphs**: You'd only see isolated tables. KumoRFM couldn't connect user behavior to item properties or discover cross-table patterns.

#### Try It Now

```python
# Your turn: Create a graph and link the tables
# Start with just users and orders (simpler graph)
graph = rfm.LocalGraph(tables=[
    users,
    orders,
])

# TODO: Link orders to users using the user_id foreign key
# Hint: Use graph.link() with src_table="orders", fkey="user_id", dst_table="users"

# Check your answer (uncomment to verify):
# links = graph.print_links()
# print("✅ Graph created! Verify the link was added correctly.")
```

<details>
<summary>Show solution</summary>

```python
graph = rfm.LocalGraph(tables=[users, orders])
graph.link(src_table="orders", fkey="user_id", dst_table="users")
graph.print_links()  # Verify the link
```

</details>

#### 1. Select the tables:

```python
graph = rfm.LocalGraph(tables=[
    users,
    orders,
    items,
])
```

#### 2. Link the tables:

In the `orders` table (`src_table`), there exists a column named `user_id` (`fkey`), which we can use as a foreign key to link to the primary key in the `users` table (`dst_table`). You don't need to specify the primary key here since it's already known as part of the metadata of the `users` table.

```python
graph.link(src_table="orders", fkey="user_id", dst_table="users");
```

Also link from the foreign key `item_id` in the `orders` table to the `items` table.

```python
graph.link(src_table="orders", fkey="item_id", dst_table="items");
```

You can verify that graph connectivity is set up by visualizing the graph:

```python
# Requires graphviz to be installed
graph.visualize();
```

... or by printing all necessary information:

```python
graph.print_metadata()
graph.print_links()
```

You can update and modify links as needed:

```python
# Remove link:
graph.unlink(src_table="orders", fkey="user_id", dst_table="users")

# Re-add link:
graph.link(src_table="orders", fkey="user_id", dst_table="users");
```

**Why this step matters**: The graph structure enables KumoRFM to understand relationships between your data, allowing it to make predictions that leverage patterns across connected tables.

**Shortcut**: In addition, there exists a handy short-cut that lets you create a `LocalGraph` directly from a set of `pandas.DataFrame` objects, bypassing the step of manual `LocalTable` creation:

```python
graph = rfm.LocalGraph.from_data({
    'users': users_df,
    'orders': orders_df,
    'items': items_df,
}, infer_metadata=True)
```

---

### Step 7. Write a predictive query

You are now ready to plug your graph into KumoRFM to make predictions!

The great thing about the graph is that it's a one-time setup—once it's in place, you can generate a variety of predictions from it and power many business use cases.

```python
model = rfm.KumoRFM(graph)
```

**Note**: The data is synthetic, and the query and results are intended for demo purposes. We encourage you to benchmark the model using your own data.

#### PQL: How you talk to your model

PQL (Predictive Query Language) lets you describe ML tasks in SQL-like syntax. If you know SQL, picking up PQL is straightforward.

**Query Structure**:
```
PREDICT [what to predict]
FOR [which entities]
ASSUMING [optional conditions]
```

#### How PQL Queries Work

**Concept**: PQL translates business questions into machine learning predictions by describing what to predict, for which entities, and under what conditions.

**Why this matters**: Instead of training separate models for each prediction task, you write queries that:
1. **Specify the prediction target**: What do you want to know? (e.g., "revenue in next 30 days")
2. **Identify the entities**: Who or what are you predicting for? (e.g., "item_id=42")
3. **Add conditions** (optional): Filter to specific scenarios (e.g., "only active users")

**Mental model**: Think of PQL as a translator between business language and ML predictions. You describe what you want in business terms, and KumoRFM uses the graph structure to find patterns and generate predictions.

**How it works internally**:
1. KumoRFM parses your query to understand the prediction task
2. It traverses the graph to gather relevant data (user history, item properties, etc.)
3. It applies pre-trained models to identify patterns
4. It generates predictions based on learned patterns

Learn more about writing all kinds of PQLs from [documentation](https://docs.kumo.ai).

**PQL tutorial notebook**: [Open in Colab](https://colab.research.google.com)

---

#### Example 1A: Forecast 30-day product demand

**Problem**: Inventory managers need to predict which products will generate revenue in the next 30 days to optimize stock levels. Stockouts lose sales, while overstock ties up capital.

**Solution**: Use KumoRFM to predict revenue for specific items based on historical order patterns.

**Query**:
```python
query = "PREDICT SUM(orders.price, 0, 30, days) FOR items.item_id=42"
df = model.predict(query)
display(df)
```

**How to interpret the result**:
- **ENTITY**: The item with `item_id=42`
- **ANCHOR_TIMESTAMP**: Assuming predicting at anchor timestamp 2024-09-19, what's happening between (2024-09-19, 2024-10-18]? By default, `anchor_time` is the mbopmum timestamp on the temporal graph.
- **TARGET_PRED**: How much revenue `item_id=42` generates in the next 30 days.

**Use the result**: If predicted revenue is high, increase stock orders. If low, let inventory run down.

---

#### Example 1B: Forecast 30-day product demand, with an anchor_time

**Problem**: You want to evaluate model performance by simulating what predictions would have looked like at a historical point in time.

**Solution**: Set an explicit `anchor_time` to test predictions using only data available up to that point.

By default, predictions are based on the mbopmum timestamp in your temporal graph. However, you can explicitly set a historical `anchor_time` to simulate what a prediction would have looked like at that point in time.

For instance, if `anchor_time` is "2024-09-01", the model will predict—assuming today is "2024-09-01"—the product demand in the next 30 days. KumoRFM will only use information before the `anchor_time` to avoid data leakage.

This feature can be useful when you want to evaluate model performance based on time-based splits.

```python
df = model.predict(query, anchor_time=pd.Timestamp("2024-09-01"))
display(df)
```

---

#### Example 2. Predict customer churn

**Problem**: Customer success teams need to identify users at risk of churning (stopping their engagement) so they can intervene with personalized offers or support.

**Solution**: Predict the likelihood that users will place zero orders in the next 90 days, indicating potential churn.

**Query**:
```python
query = "PREDICT COUNT(orders.*, 0, 90, days)=0 FOR users.user_id IN (42, 123)"
df = model.predict(query)
display(df)
```

**How to interpret the result**:
- **ENTITY**: The user with `user_id=42` or `user_id=123`
- **ANCHOR_TIMESTAMP**: Assuming we are predicting at this moment in time, what's happening in the next 90 days?
- **TARGET_PRED**: Whether the event (`COUNT(orders.*, 0, 90, days)=0`) will happen (True: Event will happen; False: Event will not happen)
- **False_PROB**: The probability that the event will not happen
- **True_PROB**: The probability that the event will happen.

**Use the result**: If `True_PROB` is high (>0.7), send a personalized coupon or reach out with support to prevent churn.

---

#### Example 3. Product recommendation

**Problem**: E-commerce platforms need to show users products they're likely to buy to increase conversion rates and revenue.

**Solution**: Predict the top items a user is most likely to purchase in the next 30 days.

**Query**:
```python
query = "PREDICT LIST_DISTINCT(orders.item_id, 0, 30, days) RANK TOP 10 FOR users.user_id=123"
df = model.predict(query)
display(df)
```

**How to interpret the result**:
- **ENTITY**: The user with `user_id=123`
- **ANCHOR_TIMESTAMP**: Assuming we are predicting at this moment in time, what's happening in the next 30 days?
- **CLASS**: The items (`item_id`)
- **SCORE**: Higher score indicates higher likelihood

**Use the result**: Display these items prominently in the user's homepage or send personalized product emails.

---

#### Example 4. Infer entity attributes

**Problem**: Data quality issues leave missing values in critical fields (like user age), making customer segmentation and personalization impossible.

**Solution**: Use KumoRFM to infer missing attributes based on patterns in related data.

**Query**:
```python
query = "PREDICT users.age FOR users.user_id=8"
df = model.predict(query)
display(df)
```

**How to interpret the result**:
- **ENTITY**: the user with `user_id=8`
- **ANCHOR_TIMESTAMP**: assuming we are predicting at this moment in time
- **TARGET_PRED**: The predicted age of the user

**Use the result**: Use inferred age for customer segmentation, personalization, or completing user profiles.

---

## Next Steps

- **Explore additional notebooks**:
  - (1) [Making predictions on a single table](https://colab.research.google.com): Open in Colab
  - (2) [The ultimate handbook to leverage KumoRFM to its full potential](https://colab.research.google.com): Open in Colab
  - (3) [Explore all notebooks](https://docs.kumo.ai/notebooks)

- **Found a bug or have a feature request?**
  - Submit issues directly on [GitHub](https://github.com/kumoai/kumo-rfm). Your feedback helps us improve RFM for everyone.

- **Built something cool with RFM?**
  - Share your project on LinkedIn and tag @kumo. We regularly spotlight on our official channels—yours could be next!

---

## Summary

You've learned how to:
1. ✅ Install and authenticate with KumoRFM
2. ✅ Create tables with primary keys, time columns, and semantic types
3. ✅ Build graphs connecting your relational data
4. ✅ Write predictive queries for forecasting, churn, recommendations, and inference
5. ✅ Interpret results and use them for business decisions

**Time to value**: You can now make predictions on your own data in minutes, not weeks!

---

## Practice & Retention

### Immediate Practice (Right Now)

Test your understanding with these exercises:

- [ ] **Exercise 1**: Modify Example 1A to predict revenue for `item_id=100` instead of 42
- [ ] **Exercise 2**: Change Example 2 to predict churn for users 1, 2, and 3
- [ ] **Exercise 3**: Create a graph with your own data (even if it's just 2-3 tables)
- [ ] **Exercise 4**: Write a query to predict the top 5 items for user 42

### Follow-Up Practice (1 Week Later)

We'll help you retain what you learned:

**What to expect**:
- Quick retrieval questions about PQL syntax
- A mini-challenge using concepts from the tutorial
- Links to advanced examples and patterns

**How to prepare**:
- Try applying KumoRFM to a real project this week
- Note any questions or challenges you encounter
- Review the examples if you get stuck

### Spaced Review (1 Month Later)

**Advanced patterns and optimizations**:
- Multi-table graph strategies
- Optimizing query performance
- Handling large datasets
- Real-world case studies

**Common mistakes and how to avoid them**:
- Primary key errors and how to debug them
- Time column formatting issues
- Semantic type selection guidelines
- Graph linking best practices

**Stay updated**:
- Subscribe to our newsletter for new features
- Join our community for tips and examples
- Check our blog for advanced tutorials

---

## Accessibility

This documentation is designed to be accessible to all users:

- **Alt text for diagrams**: All visual diagrams include descriptive alt text for screen readers
- **Keyboard navigation**: All interactive elements are keyboard accessible
- **Color contrast**: Diagrams use high-contrast colors (WCAG AA compliant)
- **Screen reader support**: Code examples include semantic markup
- **Transcripts**: Video content (if added) includes full transcripts

**Report accessibility issues**: [accessibility@kumo.ai](mailto:accessibility@kumo.ai)

---

## Help Us Improve

### Quick Feedback

Your feedback helps us improve this tutorial:

- [ ] This section was clear
- [ ] This section was confusing
- [ ] I got stuck at: _________________

### Completion Check

After finishing, test your understanding:

- [ ] I can create a graph from my own data
- [ ] I can write a predictive query
- [ ] I understand when to use different semantic types
- [ ] I can interpret prediction results
- [ ] I know how to troubleshoot common issues

### Share Your Experience

- [Submit feedback form](https://forms.kumo.ai/feedback)
- [Report a bug on GitHub](https://github.com/kumoai/kumo-rfm/issues)
- [Request a feature](https://github.com/kumoai/kumo-rfm/discussions)

**Thank you for helping us improve!** 🎉

