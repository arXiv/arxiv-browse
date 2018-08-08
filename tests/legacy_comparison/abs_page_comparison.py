import asyncio

import aiohttp

# Should end with /
ng_abs_base_url = 'http://localhost:5000/abs/'

# Should end with /
legacy_abs_base_url = 'https://beta.arxiv.org/abs/'


# get both pages, get response.text, parse, return (yield?) comparison report.

async def fetch_and_compare_abs(paperid, compare_res_fn):
    ng_url = ng_abs_base_url + paperid
    legacy_url = legacy_abs_base_url + paperid

    async with aiohttp.ClientSession() as client:
        ng_res = await client.get(ng_url)
        legacy_res = await client.get(legacy_url)
        return await compare_res_fn(ng_url=ng_url, legacy_url=legacy_url, ng_res=ng_res, legacy_res=legacy_res,
            paperid=paperid)


async def compare_res(ng_url=None, legacy_url=None,
                      ng_res=None, legacy_res=None,
                      paperid=None):
    print( f'Paper: {paperid} ng_url:{ng_url} status: {ng_res.status} legacy_url: {legacy_url} status: {legacy_res.status}')


paperids = [ '0704.0001']
futures = [fetch_and_compare_abs(paperid, compare_res) for paperid in paperids]

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(futures))
