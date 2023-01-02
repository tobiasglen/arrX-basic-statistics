import argparse
from GenerateStats import GenerateStats

parser = argparse.ArgumentParser()
parser.add_argument('--type', type=str, choices=['radarr', 'sonarr'], help='Type of arr application', required=True)
parser.add_argument('--host', type=str, help='Sonarr/Radarr instance url', required=True)
parser.add_argument('--port', type=str, help='Sonarr/Radarr instance port', default=443, required=True)
parser.add_argument('--api', type=str, help='Sonarr/Radarr instance api key', required=True)
# Optional arguments
parser.add_argument('--year', type=int, help='Year to review', default=2022)
parser.add_argument('-sm', '--start-month', type=int, help='Month to start from', default=1, choices=range(1, 13))
parser.add_argument('-em', '--end-month', type=int, help='Month to end at', default=12, choices=range(1, 13))
parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output', default=False)
args = parser.parse_args()

if __name__ == '__main__':
    # create the config object
    arrInstance = GenerateStats(host=args.host, port=args.port, api_key=args.api, review_year=args.year, start_month=args.start_month, end_month=args.end_month, verbose=args.verbose, app_type=args.type)

    # Verify that the arr instance is up, specified type is correct, and the api key is valid
    if not arrInstance.verify_arr():
        print('Exiting...')
        exit(1)

    # Generate the stats
    arrInstance.make_request_for_history()

    if len(arrInstance.get_history()) == 0:
        quit('No history found. Exiting...')

    # ----------------- LOOP ----------------- #
    # Here we loop through the json response and process the data
    for item in arrInstance.get_history():
        arrInstance.add_to_dict(target_dict=arrInstance.release_groups, target_key=item.get('data', {}).get('releaseGroup', 'Unknown'))
        arrInstance.add_to_dict(target_dict=arrInstance.indexers, target_key=item.get('data', {}).get('indexer', 'Unknown'))
        arrInstance.add_to_dict(target_dict=arrInstance.source_types, target_key=item.get('quality', {}).get('quality', {}).get('source', 'Unknown') + '-' + str(f"{item.get('quality', {}).get('quality', {}).get('resolution')}p"))
        arrInstance.add_to_dict(target_dict=arrInstance.download_methods, target_key=f'{"torrent" if item.get("data", {}).get("protocol") == "2" else "usenet"}')

        arrInstance.byte_total_size += int(item.get('data', {}).get('size', 0))

        try:
            arrInstance.total_repacks += 1 if item['quality']['revision']['isRepack'] else 0
        except KeyError:
            pass
    # ------------------ END ------------------ #

    # Print the results
    print(f'Total Grabs: {arrInstance.total_grabs}')
    print(f'Total Repacks: {arrInstance.total_repacks}')
    print(f'TB Size: {arrInstance.calculate_tb_size()}')
    print(arrInstance.get_most_common_keys(target_dict=arrInstance.release_groups, num_to_return=10))
    print(arrInstance.get_most_common_keys(target_dict=arrInstance.indexers, num_to_return=10))
    print(arrInstance.get_most_common_keys(target_dict=arrInstance.source_types, num_to_return=10))
    print(arrInstance.get_most_common_keys(target_dict=arrInstance.download_methods, num_to_return=10))

    if args.verbose:
        # Print a string representation of the config object
        print(arrInstance.__str__())
