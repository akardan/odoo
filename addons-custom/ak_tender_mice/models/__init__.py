# -*- coding: utf-8 -*-
# Model yükleme sırası önemli: bağımlılık olmayan önce yüklenmeli
from . import tender_scenario_date       # bağımlılık yok
from . import tender_scenario            # scenario_date'e bağlı
from . import tender_scenario_line       # scenario'ya bağlı
from . import tender_mice_extension      # scenario'ya bağlı
from . import purchase_order_line_extension  # en son
