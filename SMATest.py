import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.style.use("seaborn")


class SMATest:

    def __init__(self, FX, SMAS, SMAL, start, end):
        self._FX = FX
        self._SMAS = SMAS
        self._SMAL = SMAL
        self._start = start
        self._end = end
        self._results = None
        self._data = self.setup_data()
        self._data = self.prepare_data()


    # general setup of data
    def setup_data(self):
        # TODO: Be able to SELECT ticker from online source?
        df = pd.read_csv("forex_pairs.csv", parse_dates = ["Date"], index_col = "Date")
        if self._FX == "AUDEUR":
            df = df["AUDEUR=X"].to_frame().dropna()
        elif self._FX == "EURUSD":
            df = df["EURUSD=X"].to_frame().dropna()
        elif self._FX == "USDGBP":
            df = df["USDGBP=X"].to_frame().dropna()
        else:
            print("Please choose AUDEUR, EURUSD, or USDGBP")
            return None

        df = df.loc[self._start:self._end].copy()
        df.rename(columns={f"{self._FX}=X":"price"}, inplace=True)

        df["returns"] = np.log(df.price.div(df.price.shift(1)))
        return df

    # specific strategy preparation
    def prepare_data(self):
        df = self._data.copy()
        df["SMAS"] = df.price.rolling(self._SMAS).mean()
        df["SMAL"] = df.price.rolling(self._SMAL).mean()
        return df

    def get_data(self):
        return self._data

    def get_results(self):
        return self._results

    def set_params(self, SMAS = None, SMAL = None):
        if SMAS is not None:
            self._SMAS = SMAS
            self._data["SMAS"] = self._data["price"].rolling(self._SMAS).mean()
        if SMAL is not None:
            self._SMAL = SMAL
            self._data["SMAL"] = self._data["price"].rolling(self._SMAL).mean()

    def test_sma(self):

        data = self._data.copy()

        data["position"] = np.where(data["SMAS"] > data["SMAL"], 1, -1)
        data["strategy"] = data.position.shift(1) * data["returns"]
        data.dropna(inplace=True)

        data["creturns"] = data["returns"].cumsum().apply(np.exp)
        data["cstrategy"] = data["strategy"].cumsum().apply(np.exp)
        self._results = data

        performance = data["cstrategy"].iloc[-1]
        # out_performance is our strats performance vs a buy and hold on the interval
        out_performance = performance - data["creturns"].iloc[-1]

        return (performance, out_performance)

    def optimize_sma(self):

        # try all possibilities and maximize the return
        print("Attempting all possibilities. This will take a while.")
        max_return = float('-inf')
        best_df = None
        GSMAS = -1
        GSMAL = -1

        for SMAS in range(10,50):

            if SMAS == 13: print("25%...")
            if SMAS == 25: print("50%...")
            if SMAS == 38: print("75%...")

            for SMAL in range(100,252):

                self.set_params(SMAS, SMAL)
                current_return = self.test_sma()[0]

                if current_return > max_return:
                    max_return = current_return
                    best_df = self._data
                    GSMAS = SMAS
                    GSMAL = SMAL

        self.set_params(GSMAS, GSMAL)
        self.test_sma()

        return (max_return, GSMAS, GSMAL)

    def plot_results(self):
        if self._results is not None:
            title = f"{self._FX} | SMAS {self._SMAS}, SMAL {self._SMAL}"
            self._results[["creturns", "cstrategy"]].plot(title=title, figsize=(12, 8))
            plt.show()
        else:
            print("Please run test_sma() or optimize_sma().")