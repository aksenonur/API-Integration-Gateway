-- =====================================================================
-- Advanced SQL Performance & Business Intelligence Suite
-- =====================================================================

-- 1. Sales Performance & Cumulative Revenue Analysis (Window Functions)
SELECT 
    order_id,
    customer_id,
    order_date,
    amount,
    SUM(amount) OVER (PARTITION BY customer_id ORDER BY order_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total_revenue,
    AVG(amount) OVER (PARTITION BY customer_id ORDER BY order_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_amount
FROM 
    orders;

-- 2. Customer Segmentation via RFM-Style CTE
WITH CustomerMetrics AS (
    SELECT 
        customer_id,
        COUNT(order_id) AS total_orders,
        SUM(amount) AS lifetime_value,
        MAX(order_date) AS last_order_date
    FROM 
        orders
    GROUP BY 
        customer_id
),
SegmentedCustomers AS (
    SELECT 
        customer_id,
        total_orders,
        lifetime_value,
        last_order_date,
        NTILE(4) OVER (ORDER BY lifetime_value DESC) as spending_quartile
    FROM 
        CustomerMetrics
)
SELECT 
    customer_id,
    total_orders,
    lifetime_value,
    last_order_date,
    CASE 
        WHEN spending_quartile = 1 THEN 'VIP Tier'
        WHEN spending_quartile = 2 THEN 'Gold Tier'
        WHEN spending_quartile = 3 THEN 'Silver Tier'
        ELSE 'Standard Tier'
    END AS customer_tier
FROM 
    SegmentedCustomers;

-- 3. Performance Optimization: Strategic Indexing
CREATE INDEX IF NOT EXISTS idx_orders_customer_date 
ON orders (customer_id, order_date DESC);

CREATE INDEX IF NOT EXISTS idx_orders_amount 
ON orders (amount);
