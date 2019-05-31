import sys
import requests
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from utils import find_and_save_10K_to_folder, find_and_save_10Q_to_folder, find_and_save_20F_to_folder
from utils import get_historical_stock_price, get_reports_list, estimate_stock_split_adjustments
from valuation_funcs import calculate_cagr_of_time_series, calc_growth_at_normalized_PE, calc_owner_earnings
from xbrl_parser import XBRL
from ipdb import set_trace

parser = argparse.ArgumentParser(description='Optional app description')
parser.add_argument('--ticker', '-t', type=str,
                    help='The ticker of the stock you wish to analyze')
parser.add_argument('--download', '-d', action='store_true',
                    help='A boolean switch')
parser.add_argument('--foreign', '-f', action='store_true',
                    help='A boolean switch')

args = parser.parse_args()


def load_all_historical_10K(ticker, download_latest=True, foreign=False):
    ticker = ticker.lower()
    if foreign:
        report_type = '20-F'
        if download_latest:
            find_and_save_20F_to_folder(ticker, number_of_documents=10)
    else:
        report_type = '10-K'
        if download_latest:
            find_and_save_10K_to_folder(ticker, number_of_documents=10)

    files = get_reports_list(ticker, report_type=report_type)
    if len(files) <= 1:
        print(
            'could not find enough %s data. download by adding the argument "-d"' % ticker)
        sys.exit()
    xbrl = XBRL()
    for file in files:
        xbrl.load_YTD_xbrl_file(file)
    return xbrl.get_data_df()


def load_latest_quarters(ticker, download_latest=True, foreign=False):
    ticker = ticker.lower()
    if download_latest:
        find_and_save_10Q_to_folder(ticker, number_of_documents=5)
    files_10q = get_reports_list(ticker, report_type='10-Q')
    if len(files_10q) <= 1:
        print('could not find %s quarters reports - so no TTM data' % ticker)
        return None
    files_10k = get_reports_list(ticker, report_type='10-K')
    xbrl = XBRL()
    for file in files_10k:
        xbrl.load_10Q_xbrl_file(file)
    for file in files_10q:
        xbrl.load_10Q_xbrl_file(file)
    return xbrl.get_data_df()


def get_TTM_data(ticker, download_latest=True, foreign=False):
    data = load_latest_quarters(ticker, download_latest, foreign)
    if data is None:
        return None
    data.index = pd.to_datetime(data.index)
    data.sort_index(inplace=True)
    data = data.iloc[-4:]
    data.loc['TTM'] = data.sum(skipna=False)
    data.loc['TTM']['NumberOfDilutedShares'] = data.iloc[-2]['NumberOfDilutedShares']
    data.loc['TTM']['NumberOfShares'] = data.iloc[-2]['NumberOfShares']
    data.loc['TTM']['StockholdersEquity'] = data.iloc[-2]['StockholdersEquity']
    return data.loc['TTM']


def calculate_ratios(data, ticker):
    ratios = pd.DataFrame()
    ratios['RevenuePerShare(Diluted)'] = data['Revenues'].divide(
        data['NumberOfDilutedSharesAdjusted'])
    ratios['EarningPerShare(Diluted)'] = data['NetIncomeLoss'].divide(
        data['NumberOfDilutedSharesAdjusted'])
    ratios['BookValuePerShare'] = data['StockholdersEquity'].divide(
        data['NumberOfSharesAdjusted'])
    ratios['FreeCashFlowPerShare(Diluted)'] = (data['CashFlowFromOperations'] -
                                               data['CapitalExpenditure']).divide(data['NumberOfDilutedSharesAdjusted'])
    ratios['P/E'] = data['StockPrice'].divide(
        ratios['EarningPerShare(Diluted)'])
    return ratios


def main():
    ticker = args.ticker
    data = load_all_historical_10K(ticker, args.download, args.foreign)
    data = data.iloc[1:]
    data.loc['TTM'] = get_TTM_data(ticker, args.download, args.foreign)
    data['NumberOfDilutedSharesAdjusted'] = estimate_stock_split_adjustments(
        data['NumberOfDilutedShares'])
    data['NumberOfSharesAdjusted'] = estimate_stock_split_adjustments(
        data['NumberOfShares'])
    data['NumberOfDilutedSharesAdjusted'].fillna(
        data['NumberOfSharesAdjusted'], inplace=True)
    years = int(data.index[-2] - data.index[0] + 1)
    daily_prices = get_historical_stock_price(ticker, years)

    monthly_prices = daily_prices.close.resample('M').last()
    monthly_idxs = monthly_prices.index.to_list()
    # the last sample should be of the current date
    monthly_idxs[-1] = daily_prices.index[-1]
    monthly_prices.index = monthly_idxs

    yearly_prices = daily_prices.close.resample('Y').last()
    yearly_prices.drop(yearly_prices.tail(1).index, inplace=True)
    yearly_prices.index = yearly_prices.index.year

    data['StockPrice'] = yearly_prices
    data.loc['TTM']['StockPrice'] = daily_prices.iloc[-1].close
    print('-------------------------------------------------------------------------------------')
    print('--------------------------------Fundamental data:------------------------------------')
    print('-------------------------------------------------------------------------------------')
    print(data.transpose())
    print()
    print('-------------------------------------------------------------------------------------')
    print('------------------------------Key growth indicators:---------------------------------')
    print('-------------------------------------------------------------------------------------')
    ratios = calculate_ratios(data, ticker)

    print(ratios.transpose())
    print()
    print('-------------------------------------------------------------------------------------')
    print('Revenue Per Share (Diluted) Growth:')
    revenue_per_share_growth = calculate_cagr_of_time_series(
        ratios['RevenuePerShare(Diluted)'])
    print(revenue_per_share_growth)
    print()
    print('-------------------------------------------------------------------------------------')
    print('Earning Per Share (Diluted) Growth:')
    eps_growth = calculate_cagr_of_time_series(
        ratios['EarningPerShare(Diluted)'])
    print(eps_growth)
    print()
    print('-------------------------------------------------------------------------------------')
    print('Book Value Per Share Growth:')
    book_value_per_share_growth = calculate_cagr_of_time_series(
        ratios['BookValuePerShare'])
    print(book_value_per_share_growth)
    print()
    print('-------------------------------------------------------------------------------------')
    print('Free Cash Flow Per Share (Diluted) Growth:')
    free_cash_flow_growth = calculate_cagr_of_time_series(
        ratios['FreeCashFlowPerShare(Diluted)'])
    print(free_cash_flow_growth)
    print()
    print()
    print('-------------------------------------------------------------------------------------')
    print('Latest Stock Price: %.2f' % daily_prices.iloc[-1].close)
    print('-------------------------------------------------------------------------------------')
    print('Value estimation with "Growth At Normalized P/E" technique:')
    print('-------------------------------------------------------------------------------------')

    cagrs = revenue_per_share_growth.loc['CAGR'].values.tolist() + eps_growth.loc['CAGR'].values.tolist(
    ) + book_value_per_share_growth.loc['CAGR'].values.tolist() + free_cash_flow_growth.loc['CAGR'].values.tolist()
    valid_cagrs = []
    for cagr in cagrs:
        try:
            cagr_value = int(cagr[:-1])
            valid_cagrs.append(cagr_value)
        except:
            continue
    # capping the default growth rate estimation in 5-20% range
    GR_default = min(max(np.mean(valid_cagrs), 5), 20)
    GR_estimation = input(
        'Estimate growth rate in %% (if nothing entered, %d%% is taken): ' % GR_default)
    GR_estimation = int(GR_estimation or GR_default)
    pes = ratios['P/E'].values
    pes = pes[~np.isnan(pes)]
    default_pe_estimation = max(np.median(pes), 5) * 1.1
    normalized_pe_estimation = input(
        "Estimate normalized P/E estimation (if nothing entered, %.2f is taken):" % default_pe_estimation)
    normalized_pe_estimation = float(
        normalized_pe_estimation or default_pe_estimation)
    eps_ttm = ratios.loc['TTM']['EarningPerShare(Diluted)']
    if np.isnan(eps_ttm):
        eps_ttm = ratios.iloc[-2]['EarningPerShare(Diluted)']
    print("Growth rate estimation: %d%%, future P/E estimation: %.2f" %
          (GR_estimation, normalized_pe_estimation))
    print("Fair value is estimated in the range of $%.2f - $%.2f" %
          (calc_growth_at_normalized_PE(eps_ttm, normalized_pe_estimation, GR_estimation)))

    print('-------------------------------------------------------------------------------------')
    print()
    print()
    print('Value estimation with "Owner Earnings" technique:')
    print('-------------------------------------------------------------------------------------')
    owner_earnings = calc_owner_earnings(data.iloc[-2])
    if owner_earnings is not None:
        market_cap = daily_prices.iloc[-1].close * \
            data.iloc[-2]['NumberOfShares']
        print('10 years of owner earnings: %d' % (10 * owner_earnings))
        print('Market Cap: %d' % market_cap)
        print("Owner earnings ratio (>1.0 is good): %.2f" %
              (10 * owner_earnings / market_cap))
    print('-------------------------------------------------------------------------------------')
    print()
    print()
    # set_trace()


if __name__ == "__main__":
    main()
