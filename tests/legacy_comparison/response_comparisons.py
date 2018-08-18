import logging

from tests.legacy_comparison.comparison_types import res_arg_dict


def compare_status(res_arg: res_arg_dict) -> str:
    if res_arg['ng_res'].status_code == 200 and res_arg['legacy_res'].status_code == 200:
        res = f'200 HTTP status for both {res_arg["ng_url"]} and {res_arg["legacy_url"]}'
        # logging.info(res)
        return res
    else:
        res = f'HTTP status for {res_arg["ng_url"]} was {res_arg["ng_res"].status_code} ' \
              f'and for {res_arg["legacy_url"]} was {res_arg["legacy_res"].status_code}'
        logging.warning(res)
        return res
