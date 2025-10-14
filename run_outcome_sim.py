from outcome_oracle import attribute_shopify_order, settle_payout

def main():
    user = "demo_user"
    order_id = "ORD123"
    # simulate attribution from Shopify order webhook
    print("ATTRIBUTION:", attribute_shopify_order(user, order_id, rev_usd=126.00, cid="demo-cid-1"))
    # simulate settlement/payout
    print("PAID:", settle_payout(user, order_id, payout_usd=6.30, cid="demo-cid-1"))  # e.g., 5% share
if __name__ == "__main__":
    main()
