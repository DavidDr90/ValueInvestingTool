US_GAPP_TAGS_LIST = ['EarningsPerShareDiluted',
                     'EarningsPerShareBasic',
                     'GrossProfit',
                     'NetIncomeLoss',
                     'IncomeTaxExpenseBenefit',
                     'StockholdersEquity',
                     'CapitalExpenditure',
                     'CashFlowFromOperations',
                     'Revenues',
                     'CostOfGoodsAndServicesSold',
                     'SellingGeneralAndAdministrativeExpense',
                     'ResearchAndDevelopmentExpense',
                     'DepreciationAndAmortization',
                     'IncreaseDecreaseInAccountsPayable',
                     'IncreaseDecreaseInAccountsReceivable',
                     'OperatingIncomeLoss',
                     'LongTermDebtNoncurrent',
                     'NumberOfDilutedShares',
                     'NumberOfShares']

ALTERNATIVE_TAG_NAMES = {'Revenues': ['SalesRevenueNet', 'SalesRevenueGoodsNet', 'RevenueFromContractWithCustomerIncludingAssessedTax', 'RevenueFromContractWithCustomerExcludingAssessedTax'],
                         'CashFlowFromOperations': 'NetCashProvidedByUsedInOperatingActivities',
                         'NetIncomeLoss': ['NetIncomeLossAvailableToCommonStockholdersBasic', 'ProfitLoss'],
                         'CapitalExpenditure': ['PaymentsToAcquirePropertyPlantAndEquipment', 'PaymentsToAcquireProductiveAssets'],
                         'CostOfGoodsAndServicesSold': 'CostOfRevenue',
                         'DepreciationAndAmortization': 'DepreciationDepletionAndAmortization',
                         'EarningsPerShareDiluted': 'EarningsPerShareBasicAndDiluted',
                         'EarningsPerShareBasic': 'EarningsPerShareBasicAndDiluted',
                         'NumberOfDilutedShares': ['WeightedAverageNumberOfDilutedSharesOutstanding', 'WeightedAverageNumberOfShareOutstandingBasicAndDiluted'],
                         'NumberOfShares': ['WeightedAverageNumberOfSharesOutstandingBasic', 'WeightedAverageNumberOfShareOutstandingBasicAndDiluted']}
