# HOW TO USE utau2db

つかいかた

## 手順

1.  MIDIとかMusicXMLからUSTをつくる。
2.  UTAUでUSTを編集する。「っ」の原音設定がされないと不便そう。
3.  utau2dbをつかう。
4.  ラベルのチェックをする。
5.  MusicXMLから生成したLABと比較する。

### UTAUでの手順

1.  プラグイン「おま☆かせ2020」で連続音にする。（先行発声はとりあえず100でよろしく）
2.  調教したければする。
3.  全選択して 本体機能「パラメータ自動調整」を実行（STPとかをUSTに書き込むため）
4.  STPとか先行発声とかオーバーラップを編集したければする。
5.  USTから音声を出力する。

### ust2db での作業

1.  `python ust2db.py` で起動。
2.  USTがあるフォルダを指定して実行。
3.  LABが生成される。エラー出力を注意して読んでね。
4.  LABを目視できるように、setParam用のiniも出力される。

### ラベルのチェック

1.  oto2labのtoolのlab_invalid_timeでチェック
2.  oto2labのtoolのgenerate_label_from_musicxmlで比較用LAB生成
3.  oto2labのtoolのlab_set_start_silで先頭の休符を統一

### NNSVSで動作チェック

1.  oto2labのtoolのust_bpm_and_rangeで音域調査
2.  nnsvsのconfig.pyに周波数範囲（音域から推定）を書き込む
3.  頑張ってくれ
