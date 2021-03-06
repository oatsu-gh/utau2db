# utau2db

 UTAU音源を歌唱データベース化するツール

## 目的

-   UTAU音源を歌唱データベースに移植する。
-   NNSVSなどの機械学習系音声合成ソフトの動作チェックやテストにつかいたい。

## 開発環境

-   Windows 10 (2004)
-   Python3.8
-   utaupy 1.7.0

### UTAUの音声を使うメリット

-   歌い癖とかを自由に編集できる。
-   音声ファイルを際限なく作成できる。
-   歌詞が意味を持たなくてよい。ランダム文字列も可。
-   人間の歌唱が困難な音程変化や音域に対応できる。

## 手法

1.  MIDIまたはMusicXMLからUSTを生成する。
2.  生成したUSTを用いて歌唱音声を出力する。
3.  原音設定から音素ラベル位置を決定し、LAB(音素ラベル) を生成する。
4.  MIDIまたはMusicXMLのうち、欠けているほうを補完する。

## 各種仕様

### UST

-   連続音音源を想定
-   子音速度100を想定

### LAB

-   UTAUの原音設定に従うため、音素の区切り位置は既存の歌唱データベースと異なる。
-   100 ns 単位の音素ラベルを生成する。
-   音素表記は Sinsy を基本としたものを用いる。

### MusicXML

-   ブレス記号なし
