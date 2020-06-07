import argparse


def parse_init():
    parser = argparse.ArgumentParser(description='ZipHaffman')
    parser.add_argument(
        '-f', '--file',
        nargs=1,
        required=True,
        help='Name of the binary file.'
    )
    args = parser.parse_args()
    file = args.file[0]
    if '.' in file and file.rsplit('.', 1)[-1] == 'zmh':
        return file, True
    else:
        return file, False


def get_distribution(file):
    model = dict()
    with open(file, 'rb') as f:
        b = f.read(1)
        while b != b'':
            if b not in model:
                model[b] = {"num": 1, "encode": 0, "len_encode": 0}
            else:
                model[b]["num"] += 1
            b = f.read(1)
    return model


def tree(model):
    if len(model) == 1:
        for key in model.keys():
            model[key]['len_encode'] = 1
        return model
    # print(model)
    tree = [([key], value["num"]) for key, value in model.items()]
    tree = sorted(tree, key=lambda item: item[1])
    # print("tree:", tree)
    while len(tree) > 2:
        elem_1 = tree.pop(0)
        elem_2 = tree.pop(0)
        tree.append((elem_1[0] + elem_2[0], elem_1[1] + elem_2[1]))
        # print("\ntree:", tree)
        # print(elem_1[0])
        for elem in elem_1[0]:
            model[elem]['encode'] = model[elem]['encode']
            model[elem]['len_encode'] += 1
        for elem in elem_2[0]:
            model[elem]['encode'] = (1 << model[elem]['len_encode']) + model[elem]['encode']
            model[elem]['len_encode'] += 1
        tree = sorted(tree, key=lambda item: item[1])
        # print("\nmodel:", model)
        # print("\ntree:", tree)
    for elem in tree[0][0]:
        model[elem]['encode'] = model[elem]['encode']
        model[elem]['len_encode'] += 1
    for elem in tree[1][0]:
        model[elem]['encode'] = (1 << model[elem]['len_encode']) + model[elem]['encode']
        model[elem]['len_encode'] += 1
    # print(model)
    return model


def first_iter(file):
    model = get_distribution(file)
    if len(model) == 0:
        return None
    return tree(model)


def fill_model(f, model):
    max_len_encode = (max(model.values(), key=lambda item: item["len_encode"])['len_encode'] + 7) // 8
    # print(max_len_encode)
    f.write(len(model).to_bytes(1, "big"))
    f.write(max_len_encode.to_bytes(1, "big"))
    for key, value in model.items():
        f.write(key)
        f.write(value['encode'].to_bytes(max_len_encode, "big"))
        f.write(value['len_encode'].to_bytes(1, "big"))
    return 0


def second_iter(file, model):
    s = 0
    s_len = 0
    with open(file, "rb") as rf:
        with open(file + '.zmh', 'wb') as wf:
            fill_model(wf, model)
            b = rf.read(1)
            while b != b'':
                s = (s << model[b]["len_encode"]) + model[b]["encode"]
                s_len = s_len + model[b]["len_encode"]
                if s_len >= 8:
                    while s_len >= 8:
                        temp = s >> (s_len - 8)
                        wf.write(temp.to_bytes(1, 'big'))
                        s = s % 2**(s_len - 8)
                        s_len = s_len - 8
                b = rf.read(1)
            # print(s)
            if s_len > 0:
                wf.write(s.to_bytes(1, 'big'))
            wf.write(s_len.to_bytes(1, "big"))
    return 0


def encode(file):
    model = first_iter(file)
    if model is None:
        f = open(file + '.zmh', 'wb')
        f.close()
        return 0
    second_iter(file, model)
    # print("model:", model)
    return 0


def get_model(f):
    model = dict()
    len_model = f.read(1)
    if len_model == b'':
        print("Warning: empty file")
        return None, None
    len_model = int.from_bytes(len_model, "big")
    max_len_encode = f.read(1)
    if max_len_encode == b'':
        exit("Error: no encoding length")
    max_len_encode = int.from_bytes(max_len_encode, "big")
    b = f.read(1)
    if b == b'' and len_model == 0 and max_len_encode == 0:
        return {}, 0
    if b != b'' and (len_model == 0 or max_len_encode == 0):
        exit("Error: Wrong model input")
    e = f.read(max_len_encode)
    l = f.read(1)
    for i in range(len_model - 1):
        if e == b'':
            exit("Error: wrong model format.")
        if l == b'':
            exit("Error: wrong model format.")
        if b in model:
            exit("Error: Double record in model.")
        model[b] = {"encode": int.from_bytes(e, 'big'), "len_encode": int.from_bytes(l, "big")}
        b = f.read(1)
        e = f.read(max_len_encode)
        l = f.read(1)
    if e == b'':
        exit("Error: wrong model format.")
    if l == b'':
        exit("Error: wrong model format.")
    if b in model:
        exit("Error: Double record in model.")
    model[b] = {"encode": int.from_bytes(e, 'big'), "len_encode": int.from_bytes(l, "big")}
    return model, max_len_encode


def get_encoded(s, s_len, max_len_encode, model, f):
    i = 1
    #print(s_len)
    #print(s)
    while i <= s_len and s_len - i >= 8 * max_len_encode:
        temp = (s >> (s_len - i))
        #print(temp)
        len_decode = i
        search = next((key for key, value in model.items()
                       if value['encode'] == temp and value['len_encode'] == len_decode), None)
        if search:
            # print(i)
            f.write(search)
            s_len = s_len - i
            s = s % (2**s_len)
            i = 1
            continue
        i += 1
    return s, s_len


def encode_last(s, s_len, model, f):
    i = 1
    while i <= s_len:
        temp = (s >> (s_len - i))
        # print(temp)
        len_decode = i
        search = next((key for key, value in model.items()
                       if value['encode'] == temp and value['len_encode'] == len_decode), None)
        if search:
            f.write(search)
            s_len = s_len - i
            s = s % (2**s_len)
            i = 1
            continue
        i += 1
    # print(s, s_len)
    if s != 0 or s_len != 0:
        exit("Error: wrong file")
    return 0

def decode(file):
    with open(file, "rb") as rf:
        model, max_len_encode = get_model(rf)
        # print("model:", model)
        # print(len(model))
        if model is None or model == {}:
            f = open(file.rsplit('.', 1)[0], "wb")
            f.close()
            return 0
        s = 0
        s_len = 0
        with open(file.rsplit('.', 1)[0], "wb") as wf:
            b = rf.read(1)
            if b == b'':
                exit("Error: there is model but no text.")
            # print(b)
            next_b = rf.read(1)
            # print(max_len_encode)
            while next_b != b'':
                s = (s << 8) + int.from_bytes(b, "big")
                s_len += 8
                s, s_len = get_encoded(s, s_len, max_len_encode, model, wf)
                b = next_b
                next_b = rf.read(1)
            len_last = int.from_bytes(b, "big")
            if len_last != 0:
                s_len = s_len - (8 - len_last)
                temp = s >> 8
                s = s % 256
                s = (temp << len_last) + s
            encode_last(s, s_len, model, wf)
    return 0


def main():
    file, mod = parse_init()
    if mod:
        decode(file)
    else:
        encode(file)
    return 0


if __name__ == "__main__":
    main()
