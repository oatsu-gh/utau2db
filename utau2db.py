#! /ust/bin/env python3
# coding: utf-8
# Copyright (c) oatsu
"""
USTを読み取る
音源情報を取得する
音源の原音設定を取得する
NOTE: エイリアスが「a かD4」みたいな表記じゃないと困る。

USTをINIに変換する。UTAU上での原音の処理を忠実に模倣する。

つくりたいラベルの仕様----------------------------------
子音開始位置：ノート開始位置より「オーバーラップと先行発声の距離」だけ左
母音開始位置：ノート開始位置

そのために欲しいINIの仕様-------------------------------
UST上での原音のパラメータといっしょのが欲しい

原音設定の取得方法-------------------------------------
・USTから音源のPATHを取得

"""
import pathlib
# import re
from glob import glob
from os.path import basename, isdir, splitext
from pprint import pprint

import utaupy as up

# from pprint import pprint


# NOTE: SUFFIX＿LIST を音源ごとに書き換えてね。
PATH_TABLE = 'table/kana2romaji_sjis_for_oto2lab.table'
SUFFIX_LIST = ('A3', 'C5', 'D4', 'G4')
LABEL_THRESHOLD = 5  # ms

# def is_startvowel(lyric):
#     """
#     「- あ」「- い」「- う」「- え」「- お」「- を」「- ん」で始まるかを判定
#     """
#     return re.match(r'- [あいうえおをん]', lyric) is not None


# def get_suffix_from_vbdir(path_vb):
#     """
#     path_vb: UTAU音源のフォルダのパス
#     suffix の一覧を取得しようとする。
#     音源の子フォルダ名がsuffixになっていると信じる。
#     """
#     p_vb = pathlib.Path(path_vb)
#     l_suffix = [str(p).split('\\')[-1] for p in p_vb.iterdir() if p.is_dir()]
#
#     return l_suffix


# def get_gennon_setting(path_vb):
#     """
#     path_vb: UTAU音源のフォルダのパス
#     原音設定用のoto.iniをまとめた辞書を返す。
#     """
#     # 原音設定をひとつの辞書にまとめる
#     l_path_otoini = glob(f'{path_vb}/**/oto.ini', recursive=True)
#     d = {}
#     for path_otoini in l_path_otoini:
#         d.update(up.otoini.load(path_otoini).as_dict)
#     return d


def note2oto(note, t_start_ms, name_wav):
    """
    note           : utaupy.ust.Note class object
    name_wav       : Otoにセットする音声ファイル名

    先頭音だけ発声開始位置を左ブランクにする。
    ほかは 子音開始位置がオーバーラップ 母音開始位置が先行発声。
    """
    # TODO: 子音速度を取得して、子音の長さを計算しなおす。
    # 子音速度
    # try:
    #     velocity = int(note.get_by_key('Velocity'))
    #     if velocity != 100:
    #         print(' [WARN] get_consonant_duration_from_note: 未対応なので子音速度を100にしてください。')
    # except KeyError:
    #     velocity = 100

    # ラベルにするための新規Oto
    oto = up.otoini.Oto()
    # USTの出力ファイル名を新規Otoの音声ファイル名にセット
    oto.filename = name_wav
    # USTの歌詞を新規Otoのエイリアスにセット
    oto.alias = note.lyric
    # USTオーバーラップの位置を新規Otoのオーバーラップにセット
    oto.overlap = float(note.get_by_key('VoiceOverlap'))
    # USTの先行発声を新規Otoの先行発声にセット
    oto.preutterance = float(note.get_by_key('PreUtterance'))
    # USTのSTP（切り落とし）を踏まえて、原音の左ブランクを新規Otoの左ブランクにセット
    # 先行発声の値がずれているのでSTPは不要
    oto.offset = t_start_ms - oto.preutterance
    # USTのノート終端位置(先行発声までの時間とノート長の合計)を新規Otoの右ブランクにセット
    oto.cutoff2 = oto.offset + oto.preutterance + note.length_ms
    # 子音部固定範囲は先行発声と同じ位置に設定（USTに情報がないため）
    oto.consonant = oto.preutterance

    return oto


def ust2otoini_for_utau2db(ust, d_table, path_vb, name_wav):
    """
    utaupy.convert.ust2otoini_romaji_cv の改造版
    改変内容-------------------------------------------
    ・dtが固定値ではなく、原音設定値から取得する
    ---------------------------------------------------

    先頭音だけは発声開始位置を左ブランクにしたほうがいいと思う。
    """
    # 最終ノートが休符じゃない場合を対策
    ust.make_finalnote_R()
    # 出力するOtoIniに書き込むために、USTから出力WAVファイル名を取得 # NOTE: USTファイル名からに変更
    # name_wav = ust.setting.get_by_key('OutFile')
    # 原音設定をまとめた辞書
    # d_gennon = get_gennon_setting(path_vb)
    # サフィックス一覧を取得する
    # l_suffix = get_suffix_from_vbdir(path_vb)
    l_suffix = SUFFIX_LIST

    # ラベリング用OtoIni生成元にするリスト
    l_for_otoini = []
    # ノート開始時刻を記録
    t_start_ms = 0

    for note in ust.notes:
        # 原音設定を参照してNoteをOtoに変換
        oto = note2oto(note, t_start_ms, name_wav)
        if oto.alias.startswith('- '):
            if oto.alias in ['- あ', '- い', '- う', '- え', '- お', '- を', '- ん']:
                oto.preutterance = oto.overlap
            else:
                oto.overlap = min(0, oto.overlap)
        # サフィックス文字列（D4とか強とか）を削除
        for suffix in l_suffix:
            oto.alias = oto.alias.replace(suffix, '')
        # プレフィックス文字列 ('-' とか 'a' ) を削除
        oto.alias = oto.alias.split()[-1]
        # かな→ローマ字変換
        try:
            oto.alias = ' '.join(d_table[oto.alias])
        except KeyError as err:
            print(f"    [WARN] KeyError of d_table in ust2otoini_for_utau2db : '{err}'")

        # OtoIni生成用のリストに追加
        l_for_otoini.append(oto)
        # 今のノート終了位置が次のノート開始位置
        t_start_ms += note.length_ms

    otoini = up.otoini.OtoIni(l_for_otoini)
    return otoini


def main():
    """
    USTを入力させてLABを生成する。
    ついでにINIも生成しとく。
    """
    # 変換したいファイルがあるフォルダのパスを入力
    path_ustdir = input('path_ustdir     : ').strip('"')
    if isdir(path_ustdir):
        list_path_ust = glob(f'{path_ustdir}/*.ust', recursive=True)
    else:
        list_path_ust = [path_ustdir]
    # utau.exe があるフォルダを入力 # NOTE: 原音設定フォルダを手動設定にしたから無効化
    path_utauexe_dir = input('path_utauexe_dir: ').strip('"')
    # かな→ローマ字変換テーブルのパス
    path_table = PATH_TABLE
    # 変換テーブルを読み取る
    d_table = up.table.load(path_table)

    pprint(list_path_ust)

    for path_ust in list_path_ust:
        print('--------------------------------------------------------------------------------')
        print(f'  path_ust: {path_ust}')
        # ustを読み取る
        ust = up.ust.load(path_ust)
        # 原音設定のPATHをUSTから取得
        path_vb = ust.setting.get_by_key('VoiceDir').replace(
            '%VOICE%', f'{path_utauexe_dir}\\voice\\')
        print(f'  path_vb : {path_vb}')
        # suffixになりうる文字列をリストで取得
        # l_suffix = get_suffix(path_vb)
        # print(f'  l_suffix: {l_suffix}')
        # UstをOtoIniに変換
        name_wav = splitext(basename(path_ust))[0] + '.wav'
        otoini = ust2otoini_for_utau2db(ust, d_table, path_vb, name_wav)
        # INIファイルを出力
        path_ini = splitext(path_ust)[0] + '.ini'
        otoini.write(path_ini)
        print(f'  path_ini: {path_ini}')
        # そのままLABに変換
        label = up.convert.otoini2label(otoini)
        # 発声時間が負のラベルがないか検査
        label.check_invalid_time(threshold=LABEL_THRESHOLD)
        path_lab = splitext(path_ust)[0] + '.lab'
        label.write(path_lab)
        print(f'  path_lab: {path_lab}')


if __name__ == '__main__':
    print('_____ξ・ヮ・) < utau2db v1.2.0 ________')
    # print('Copyright (c) 2001-2020 Python Software Foundation')
    print('Copyright (c) 2020 oatsu')
    # 確認
    flag = input('USTのパラメータ自動調整はしましたか？(y/n): ')
    if flag == 'y':
        main()
    else:
        print('[ERROR] UTAUで「パラメータ自動調整を適用」してください。')
    input('\nPress Enter to exit.')
