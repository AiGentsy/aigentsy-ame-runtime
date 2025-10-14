from aam_queue import AAMQueue
from sdk_aam_executor import execute
from caio_orchestrator import run_play

def main():
    q = AAMQueue(executor=execute)
    # TikTok
    print("TikTok run:", run_play(q, user_id="demo_user", app="tiktok", slug="tiktok-promo-v1",
                                 context={"media":"demo.mp4","title":"Launch","cost_usd":0},
                                 autonomy_json={"level":"suggest","policy":{"block":[]}}))
    # Amazon
    print("Amazon run:", run_play(q, user_id="demo_user", app="amazon", slug="amazon-cart-nudge-v1",
                                  context={"cart_id":"demo","cost_usd":10},
                                  autonomy_json={"level":"act","policy":{"block":[]}}))
    # Shopify
    print("Shopify run:", run_play(q, user_id="demo_user", app="shopify", slug="shopify-growth-v1",
                                   context={"title":"New Drop","cost_usd":0},
                                   autonomy_json={"level":"suggest","policy":{"block":[]}}))
if __name__ == "__main__":
    main()
