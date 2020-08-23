#!python
# coding: utf-8
# Copyright (c) oatsu
"""

# NOTE: utau2db v1.0.0 のときのファイル。

USTを読み取る
音源情報を取得する
音源の原音設定を取得する
NOTE: エイリアスが「a かD4」みたいな表記じゃないと困る。

USTをINIに変換する。通常のust2iniより複雑(歌詞によってdtを変化させる必要がある)

つくりたいラベルの仕様----------------------------------
子音開始位置：ノート開始位置より「オーバーラップと先行発声の距離」だけ左
母音開始位置：ノート開始位置

そのために欲しいINIの仕様-------------------------------
①左ブランクとオーバーラップを重ねる場合の各値
左ブランク    ：ノート開始時刻 - 子音の長さ(原音設定のオーバーラップから先行発声まで)
オーバーラップ：0
先行発声      ：子音の長さ
②左ブランクとオーバーラップをずらす場合の各値
左ブランク    ：ノート開始時刻 - 2 x 子音の長さ
オーバーラップ：子音の長さ
先行発声      ：子音の長さ x 2
③左ブランクとオーバーラップをずらす場合の各値（オーバーラップを先行発声の1/3にするタイプ）
左ブランク    ：ノート開始時刻 - 1.5 x 子音の長さ
オーバーラップ：子音の長さ x 0.5
先行発声      ：子音の長さ x 1.5

原音設定の取得方法-------------------------------------
・USTから音源のPATHを取得（したい）
・原音設定のoto.iniを全部まとめた辞書にする
  この時、エイリアスに音階名が入ってるかどうか確認する必要がある
  {エイリアス1: 子音の長さ, エイリアス2: 子音の長さ, ...}
・prefix.mapを読み取ってエイリアスを確定させたい
  UTAUで連続音一括設定プラグインのprefix.map使用機能をつかってもよい


"""
import os
import pathlib
import re
from glob import glob

import utaupy as up

# from pprint import pprint


PATH_TABLE = 'table/kana2romaji_sjis_for_oto2lab.table'


def is_startvowel(lyric):
    """
    「- あ」「- い」「- う」「- え」「- お」「- を」「- ん」で始まるかを判定
    """
    return re.match(r'- [あいうえおをん]', lyric) is not None


def get_consonant_duration(path_otoini_dir):
    """
    原音設定の値を読み取る
    ・「- か」のような先頭の音は、オーバーラップの代わりに左ブランクを子音開始位置として扱い、
      先頭音の子音長のみ 先行発声 - 左ブランク とする。
    ・「- あ」「- い」「- う」「- え」「- お」「- を」「- ん」のような単音素先頭音は、
      先行発声の位置を左ブランクの位置にずらす。
    """

    list_otoini = glob(f'{path_otoini_dir}/**/oto.ini', recursive=True)
    # print('list_otoini in get_consonant_duration:')
    # pprint(list_otoini)
    # 原音設定から子音の長さを取得した辞書 {エイリアス:子音の長さ, ...}
    d_consdur = {}
    # oto.iniから値を取得して、エイリアスと子音の長さの辞書を作る
    # for path_otoini in list_otoini:
    #     otoini = up.otoini.load(path_otoini)
    #     d_temp = {oto.alias: (oto.preutterance - oto.overlap) for oto in otoini.values}
    #     d_consdur.update(d_temp)
    for path_otoini in list_otoini:
        otoini = up.otoini.load(path_otoini)
        d_consdur.update({oto.alias: (oto.preutterance - oto.overlap) for oto in otoini.values})

    # この時点で全エイリアスを網羅した辞書ができてるはず

    # 休符とかのエラーを回避
    d_consdur.update({'pau': 0.0, 'R': 0.0, '息': 0.0, 'br': 0.0, 'sil': 0.0, 'cl': 0.0})
    return d_consdur


def get_prefix(path_otoini_dir):
    """
    path_otoini_dirdir: UTAU音源のフォルダのパス
    prefix の一覧を取得しようとする。
    音源の子フォルダ名がprefixになっていると信じる。
    """
    p_vbdir = pathlib.Path(path_otoini_dir)
    l_prefix = [str(p).split('\\')[-1] for p in p_vbdir.iterdir() if p.is_dir()]

    return l_prefix


def ust2otoini_for_utau2db(ust, name_wav, d_table, d_consdur, l_prefix, replace=True):
    """
    utaupy.convert.ust2otoini_romaji_cv の改造版
    改変内容-------------------------------------------
    ・dtが固定値ではなく、原音設定値から取得する
    ---------------------------------------------------

    if len(re.findall('- あ*|- い*|- う*|- え*|- お*|- を*|- ん*', oto.alias)) > 0:
        phoneme.start -= oto.preutterance
    TODO: みたいなかんじで先頭母音のラベリング位置をずらす処理を追加したい

    UstクラスオブジェクトからOtoIniクラスオブジェクトを生成
    dt   : 左ブランク - オーバーラップ - 先行発声 - 固定範囲と右ブランク の距離
    mode : otoiniのエイリアス種別選択
    【パラメータ設定図】
      | 左ブランク          | オーバーラップ   | 先行発声       | 固定範囲       | 右ブランク     |
      |   (consdur/2) ms    |   (consdur) ms   |  (consdur) ms  |  (consdur) ms  | (length-2dt)ms |
    """
    ust.make_finalnote_R()  # 最終ノートが休符じゃない場合を対策
    # name_wav = ust.setting.get_by_key('OutFile')
    notes = ust.values
    l = []  # otoini生成元にするリスト
    t = 0  # ノート開始時刻を記録

    for note in notes[2:-1]:
        try:
            dt = d_consdur[note.lyric]
        except KeyError as err:
            print(f'    [ERROR] KeyError of d_consdur in ust2otoini_for_utau2db : {err}')
            dt = 0
        try:
            # 連続音の - とか a を削除
            suppin_lyric = note.lyric.split()[-1]
            # プレフィックス文字列（D4とか強とか）を削除
            for prefix in l_prefix:
                suppin_lyric = suppin_lyric.rstrip(prefix)
            phonemes = d_table[suppin_lyric]
        except KeyError as err:
            print(f'    [ERROR] KeyError of d_table in ust2otoini_for_utau2db : {err}')
            phonemes = note.lyric.split()

        length = note.length_ms
        oto = up.otoini.Oto()
        oto.filename = name_wav     # wavファイル名
        if replace:
            oto.alias = ' '.join(phonemes)  # エイリアスは音素ごとに空白区切り
        else:
            oto.alias = note.lyric
        oto.offset = t - (2 * dt)   # 左ブランクはノート開始位置より2段手前
        oto.overlap = 0             # オーバーラップは左ブランクに重ねる
        oto.preutterance = 2 * dt   # 先行発声はノート開始位置
        oto.consonant = min(3 * dt, length + 2 * dt)  # 子音部固定範囲は先行発声より1段後ろか終端
        oto.cutoff = -(length + 2 * dt)  # 右ブランクはノート終端、負で左ブランク相対時刻、正で絶対時刻

        # 1音素のときはノート開始位置に先行発声を配置
        if len(phonemes) == 1:
            if note.lyric.startswith('- '):
                oto.preutterance -= dt // 2

        # 2,3音素の時はノート開始位置に先行発声を配置、その手前にオーバーラップを配置
        elif len(phonemes) in (2, 3):
            oto.overlap = dt

        # 4音素以上には未対応。特殊音素と判断して1音素として処理
        else:
            print('\nERROR when setting alias : phonemes = {}-------------'.format(phonemes))
            print('1エイリアスあたり 1, 2, 3 音素しか対応していません。')
            oto.alias = ''.join(phonemes)

        l.append(oto)
        t += length  # 今のノート終了位置が次のノート開始位置

    # 最初が休符なことを想定して、
    l[0].offset = 0  # 最初の左ブランクを0にする
    l[0].overlap = 0  # 最初のオーバーラップを0にする
    l[0].preutterance = 0  # 最初の先行発声を0にする
    # l[0].cutoff2 -= 2 * dt
    otoini = up.otoini.OtoIni()
    otoini.values = l
    return otoini


def main():
    """
    USTを入力させてLABを生成する。
    ついでにINIも生成しとく。
    """
    # 変換したいファイルがあるフォルダのパスを入力
    path_ustdir = input('path_ustdir     : ').strip('"')
    list_path_ust = glob(f'{path_ustdir}/*.ust', recursive=True)
    # utau.exe があるフォルダを入力 # NOTE: 原音設定フォルダを手動設定にしたから無効化
    # path_utauexe_dir = input('path_utauexe_dir: ').strip('"')
    # 原音設定のoto.iniがあるフォルダのパスを入力
    # もとの音源と同じディレクトリ構成が良い
    path_otoini_dir = input('path_otoini_dir : ').strip('"')
    # かな→ローマ字変換テーブルのパス
    path_table = PATH_TABLE
    # 変換テーブルを読み取る
    d_table = up.table.load(path_table)

    for path_ust in list_path_ust:
        print('--------------------------------------------------------------------------------')
        print(f'path_ust: {path_ust}')
        # ustを読み取る
        ust = up.ust.load(path_ust)
        # 原音設定のPATHをUSTから取得 # NOTE: ここじゃなくて手動入力にした
        # path_otoini_dir = ust.setting.get_by_key('VoiceDir').replace('%VOICE%', f'{path_utauexe_dir}/voice/')
        print(f'path_otoini_dir : {path_otoini_dir}')
        # 各エイリアスの子音の長さを辞書で取得
        d_consdur = get_consonant_duration(path_otoini_dir)
        # pprint(d_consdur)
        # prefixになりうる文字列をリストで取得
        l_prefix = get_prefix(path_otoini_dir)
        print(f'l_prefix: {l_prefix}')
        # 変換
        name_wav = os.path.splitext(os.path.basename(path_ust))[0] + '.wav'
        # print(f'name_wav: {name_wav}')
        otoini = ust2otoini_for_utau2db(ust, name_wav, d_table, d_consdur, l_prefix)
        # INIファイルを出力
        path_ini = os.path.splitext(path_ust)[0] + '.ini'
        otoini.write(path_ini)
        print(f'path_ini: {path_ini}')
        # そのままLABに変換
        label = up.convert.otoini2label(otoini)
        path_lab = os.path.splitext(path_ust)[0] + '.lab'
        label.write(path_lab)
        print(f'path_lab: {path_lab}')


if __name__ == '__main__':
    print('_____ξ・ヮ・) < utau2db v0.0.1 ________')
    # print('Copyright (c) 2001-2020 Python Software Foundation')
    print('Copyright (c) 2020 oatsu\n')
    main()
    input('\nPress Enter to exit.')
