import time
from parser import parse_file
from search import linear_search, build_index, dict_lookup


def time_ns(func, *args):
    start = time.perf_counter_ns()
    func(*args)
    return time.perf_counter_ns() - start


def main():
    records = parse_file()
    index = build_index(records)  # built once, not counted in lookup time

    total = len(records)
    # at least 20 ids spread across the list (includes the first and last)
    sample_size = min(20, total)
    step = max(total // sample_size, 1)
    test_ids = [records[i]["id"] for i in range(0, total, step)][:sample_size]
    test_ids.append(records[-1]["id"])  # worst case for linear search

    print(f"Records: {total} | Test ids: {len(test_ids)}\n")
    print(f"{'id':>6} {'linear (ns)':>14} {'dict (ns)':>12}")

    linear_total = dict_total = 0
    for rid in test_ids:
        lin = time_ns(linear_search, records, rid)
        dic = time_ns(dict_lookup, index, rid)
        linear_total += lin
        dict_total += dic
        print(f"{rid:>6} {lin:>14} {dic:>12}")

    n = len(test_ids)
    print(f"\nAverage linear search: {linear_total / n:.0f} ns")
    print(f"Average dict lookup:   {dict_total / n:.0f} ns")
    print(f"Dict lookup was about {linear_total / max(dict_total, 1):.1f}x faster")


if __name__ == "__main__":
    main()