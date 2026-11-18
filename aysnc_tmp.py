import asyncio
# A small, offline example: gather three pieces of context concurrently.
async def get_customer_context():
    await asyncio.sleep(0.3)
    return {"customer": "Maya"}

async def get_order_context():
    await asyncio.sleep(0.3)
    return {"order_status": "shipped"}

async def get_product_context():
    await asyncio.sleep(0.3)
    return {"product": "Wireless headphones"}

async def build_support_context():
    customer, order, product = await asyncio.gather(
        get_customer_context(),
        get_order_context(),
        get_product_context(),
    )

    return {**customer, **order, **product}

result =  asyncio.run(build_support_context())
print(result)