import multiprocessing
import os

import qlib

if __name__ == "__main__":
    multiprocessing.set_start_method("fork", force=True)

    _provider = os.environ.get("QLIB_DATA_DIR", os.environ.get("QLIB_PROVIDER_URI", "~/.qlib/qlib_data/cn_data"))
    qlib.init(provider_uri=_provider)
    from qlib.data import D

    instruments = D.instruments()
    fields = ["$open", "$close", "$high", "$low", "$volume"]
    data = D.features(instruments, fields, freq="day").swaplevel().sort_index().loc["2015-01-01":].sort_index()

    data["$return"] = data.groupby(level=0)["$close"].pct_change().fillna(0)
    print(data)
    data.to_hdf("./daily_pv_all.h5", key="data")

    # Reuse already-loaded data for debug slice (avoids second D.features() call)
    debug_instruments = data.reset_index()["instrument"].unique()[:100]
    debug_data = data.swaplevel().loc[debug_instruments].swaplevel().sort_index()
    print(debug_data)
    debug_data.to_hdf("./daily_pv_debug.h5", key="data")