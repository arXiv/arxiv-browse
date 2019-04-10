from comparison_types import res_arg_dict, BadResult


def compare_status(res_arg: res_arg_dict) -> BadResult:
    if res_arg['ng_res'].status_code == 200 and res_arg['legacy_res'].status_code == 200:
        return None
    else:
        res = f'HTTP status for {res_arg["ng_url"]} was {res_arg["ng_res"].status_code} ' \
              f'and for {res_arg["legacy_url"]} was {res_arg["legacy_res"].status_code}'
        return BadResult(res_arg['paper_id'], 'compare_status', res)
