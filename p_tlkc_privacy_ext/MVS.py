import copy

import numpy as np
import multiprocessing as mp
import operator

class MVS():

    def __init__(self, T, logsimple, sensitive, cont, sensitives, bk_type, dict_safe={}):
        self.T = T
        self.logsimple = logsimple
        self.sensitive = sensitive
        self.cont = cont
        self.sensitives = sensitives
        self.dev = []
        self.bk_type = bk_type
        self.dict_safe = dict_safe


    def mvs(self, L, K, C, multiprocess, t = None):
        i = L
        while i > 0 and i < L + 1:
            i -= 1
            if t is None:
                if self.dict_safe[i][K][C]["v"] != []:
                    w = self.dict_safe[i][K][C]["w"]
                    X1 = self.dict_safe[i][K][C]["x"]
                    violating = self.dict_safe[i][K][C]["v"]
            else:
                if self.dict_safe[i][K][C][t]["v"] != []:
                    w = self.dict_safe[i][K][C][t]["w"]
                    X1 = self.dict_safe[i][K][C][t]["x"]
                    violating = self.dict_safe[i][K][C][t]["v"]
            if 'X1' in locals() and len(X1) > 0:
                count = {tuple(el): 0 for el in X1}
                prob = {tuple(v): {el: [] for el in self.sensitive} for v in X1}
                el_trace = {tuple(el): [] for el in X1}
                i += 1
                w.append([])
                violating.append([])
                prob, count, el_trace = self.prob(X1, count, el_trace, prob, i, type, first=True)
                gen = [q for q in X1 if count[tuple(q)] > 0]
                w, violating = self.w_violating(gen, count, violating, prob, K, C, w, i)
                # 10: end if
                # 11: end for
                X1.clear()
                # 12: Xi+1 ! Wi ! Wi;
                X1 = self.w_create(w, i, X1, violating, L, multiprocess)
                print("X1: " + str(len(X1)))
                i += 1
                break
            elif 'X1' in locals() and len(X1) == 0:
                i = L+1
        # 1: X1 <- set of all distinct pairs in T;
        if i == 0:
            flat_list = [item for sublist in self.T for item in sublist]
            X1 = list(set(flat_list))

            if self.bk_type == 'multiset':
                not_valid_multiset = []
                for el in X1:
                    if el[1] > L:
                        not_valid_multiset. append(el)
                for x in not_valid_multiset:
                    X1.remove(x)

            print("X1: " + str(len(X1)))
            # 2: i = 1;
            #count(q)
            #prob(q|s)
            count = {el: 0 for el in X1}
            prob = {v: {el: [] for el in self.sensitive} for v in X1}
            el_trace = {el: [] for el in X1}
            prob, count, el_trace = self.prob(X1, count, el_trace, prob, i, type)
            # 5: for all q  in Xi where |T(q)| > 0 do
            gen = [q for q in X1 if count[tuple(q)] > 0]
            violating = [[]]
            w = [[]]
            w, violating = self.w_violating(gen, count, violating, prob, K, C, w, i)
            # 10: end if
            # 11: end for
            w[0].sort(key=operator.itemgetter(1))
            X1.clear()
            # 12: Xi+1 ! Wi ! Wi;
            if self.bk_type == 'relative': #sequence time
                for iterator in range(len(w[0])):
                    candidate = w[0].pop(0)
                    for comb in w[0]:
                        if comb[1] > candidate[1]:
                            X1.append([candidate, comb])
                        elif comb[0] != candidate[0] and comb[1] == candidate[1]:
                            X1.append([candidate, comb])
                        elif comb[1] < candidate[1]:
                            X1.append([comb, candidate])
                    w[0].append(candidate)
                    iterator += 1

            elif self.bk_type == 'sequence': #sequence
                for iter in range(len(w[0])):
                    candidate = w[0].pop(0)
                    for comb in w[0]:
                        if comb[0] != candidate[0]:
                            X1.append([candidate, comb])
                        if comb[1] > candidate[1]:
                            X1.append([candidate, comb])
                        elif comb[1] < candidate[1]:
                            X1.append([comb, candidate])
                    w[0].append(candidate)
                    iter += 1
            elif self.bk_type == 'set': #set
                while len(w[0]) > 1:
                    candidate = w[0].pop(0)
                    for comb in w[0]:
                        if sorted([candidate, comb]) not in X1:
                            X1.append(sorted([candidate, comb]))
            elif self.bk_type == 'multiset': #multiset
                while len(w[0]) > 1:
                    candidate = w[0].pop(0)
                    for comb in w[0]:
                        if sorted([candidate, comb]) not in X1:
                            if comb[0] != candidate[0] and (comb[1] + candidate[1]) <= L:
                                X1.append(sorted([candidate, comb]))
            i = 1
            print("X1: " + str(len(X1)))
        # 3: while i <= L or Xi not empty do
        while i < L and len(X1) > 0:
            # 4: Scan T to compute |T(q)| and P(s|q), for all q in Xi, for all s in S;
            w.append([])
            violating.append([])
            count = {tuple(el): 0 for el in X1}
            prob = {tuple(v): {el: [] for el in self.sensitive} for v in X1}
            prob, count, el_trace = self.prob(X1, count, el_trace, prob, i, type)
            # 5: for all q  in Xi where |T(q)| > 0 do
            gen = [q for q in X1 if count[tuple(q)] > 0]
            w, violating = self.w_violating(gen, count, violating, prob, K, C, w, i)
            # 10: end if
            # 11: end for
            i += 1
            if i < L:
                X1.clear()
                # 12: Xi+1 ! Wi ! Wi;
                X1 = self.w_create(w, i-1, X1, violating, L, multiprocess)
                print("X1: " + str(len(X1)))
            # 18: i++;

        # 19: end while
        # 20: return V (T) = V1 ' · · · ' Vi−1;
        if t is None:
            self.dict_safe[i - 1][K][C]["w"] = w.copy()
            self.dict_safe[i - 1][K][C]["x"] = X1.copy()
            self.dict_safe[i - 1][K][C]["v"] = violating.copy()
        else:
            self.dict_safe[i - 1][K][C][t]["w"] = w.copy()
            self.dict_safe[i - 1][K][C][t]["x"] = X1.copy()
            self.dict_safe[i - 1][K][C][t]["v"] = violating.copy()

        violatingConj = [item for sublist in violating for item in sublist]

        return violatingConj, self.dict_safe

    def chunk(self, data, parts):
        divided = [None] * parts
        n = len(data) // parts
        for i in range(parts):
            divided[i] = data[i * n:n * (i + 1)]
        if len(data) % 2 != 0:
            divided[-1] += [data[-1]]
        return divided

    def chunkIt(self, data, num):
        avg = len(data) / float(num)
        out = []
        last = 0.0

        while last < len(data):
            out.append(data[int(last):int(last + avg)])
            last += avg

        return out

    def X1_generator_seq(self, data,i,X1,violating):
        # replace w[i] with data
        # copy X1 to Z1
        Z1 = copy.deepcopy(X1)
        for iter in range(len(data)):
            candidate = data.pop(0)
            for comb in data:
                add = False
                add2 = False
                try:
                    if candidate[0:i] == comb[0:i] and comb[i][0] != candidate[i][0]:
                        add = True
                except:
                    print(candidate)
                    print(comb)
                    print(i)

                if candidate[0:i] == comb[0:i] and comb[i][0] != candidate[i][0]:  # and \
                    # comb[i][1] >= candidate[i][1]:
                    add = True
                elif candidate[0:i] == comb[0:i] and comb[i][0] == candidate[i][0] \
                        and comb[i][1] > candidate[i][1]:
                    add = True
                elif candidate[0:i] == comb[0:i] and comb[i][0] == candidate[i][0] \
                        and comb[i][1] < candidate[i][1]:
                    add2 = True
                if add:
                    Z1.append([])
                    Z1[len(Z1) - 1] = candidate[:]
                    Z1[len(Z1) - 1].append(comb[i])
                elif add2:
                    Z1.append([])
                    Z1[len(Z1) - 1] = comb[:]
                    Z1[len(Z1) - 1].append(candidate[i])
                if add or add2:
                    if Z1[len(Z1) - 1] in Z1[0:len(Z1) - 1]:
                        del Z1[-1]
                    else:
                        # 13: for %q & Xi+1 do
                        # 14: if q is a super sequence of any v & Vi then
                        # 15: Remove q from Xi+1;
                        if len(Z1) == 0:
                            break
                        included = False
                        for v in violating[i]:
                            if all(elem in Z1[len(Z1) - 1] for elem in v):
                                for j in range(0, i + 1):
                                    if j == 0:
                                        if v[j] in Z1[len(Z1) - 1]:
                                            index = Z1[len(Z1) - 1].index(v[j])
                                        else:
                                            break
                                    else:
                                        if v[j] in Z1[len(Z1) - 1][index + 1::]:
                                            index = Z1[len(Z1) - 1].index(v[j])
                                            if j == i:
                                                included = True
                                                break
                                        else:
                                            break
                            # if all(elem in X1[len(X1) - 1] for elem in v):
                            if included:
                                del Z1[-1]
                                break
            data.append(candidate)
            iter += 1

        return Z1

    def X1_generator_relative(self,data,i,X1,violating):
        Z1 = copy.deepcopy(X1)
        for iterator in range(len(data)):
            candidate = data.pop(0)
            for comb in data:
                if candidate[0:i] == comb[0:i] and candidate[i][1] > comb[i][1]:
                    Z1.append([])
                    Z1[len(Z1) - 1] = comb[:]
                    Z1[len(Z1) - 1].append(candidate[i])
                elif candidate[0:i] == comb[0:i] and candidate[i][1] < comb[i][1]:
                    Z1.append([])
                    Z1[len(Z1) - 1] = candidate[:]
                    Z1[len(Z1) - 1].append(comb[i])
                elif candidate[0:i] == comb[0:i] and candidate[i][1] == comb[i][1] and candidate[i][1] != comb[i][1]:
                    Z1.append([])
                    Z1[len(Z1) - 1] = candidate[:]
                    Z1[len(Z1) - 1].append(comb[i])
                else:
                    break
                if Z1[len(Z1) - 1] in Z1[0:len(Z1) - 1]:
                    del Z1[-1]
                else:
                    # 13: for %q & Xi+1 do
                    # 14: if q is a super sequence of any v & Vi then
                    # 15: Remove q from Xi+1;
                    included = False
                    for v in violating[i]:
                        if len(Z1) == 0:
                            break
                        if all(elem in Z1[len(Z1) - 1] for elem in v):
                            for j in range(0, i + 1):
                                if j == 0:
                                    if v[j] in Z1[len(Z1) - 1]:
                                        index = Z1[len(Z1) - 1].index(v[j])
                                    else:
                                        break
                                else:
                                    if v[j] in Z1[len(Z1) - 1][index + 1::]:
                                        index = Z1[len(Z1) - 1].index(v[j])
                                        if j == i:
                                            included = True
                                            break
                                    else:
                                        break
                        # if all(elem in Z1[len(Z1) - 1] for elem in v):
                        if included:
                            del Z1[-1]
                            break
            data.append(candidate)
            iterator += 1

        return Z1

    def X1_generator_multiset(self, data, i, X1, violating):
        while len(data) > 0:
            candidate = data.pop()
            for comb in data:
                if candidate[0:i] == comb[0:i] and comb[i] not in candidate:
                    if comb[i][0] in [el[0] for el in candidate]:
                        continue
                    if comb[i][1] + sum([el[1] for el in candidate]) > L:
                        continue
                    X1.append([])
                    X1[len(X1) - 1] = candidate[:]
                    X1[len(X1) - 1].append(comb[i])
                    X1[len(X1) - 1] = sorted(X1[len(X1) - 1])
                    if X1[len(X1) - 1] in X1[0:len(X1) - 1]:
                        del X1[-1]
                    else:
                        # 13: for %q & Xi+1 do
                        # 14: if q is a super sequence of any v & Vi then
                        # 15: Remove q from Xi+1;
                        for v in violating[i]:
                            if len(X1) == 0:
                                break
                            if all(elem in X1[len(X1) - 1] for elem in v):
                                del X1[-1]
        return X1

    def X1_generator_set(self, data, i, X1, violating):
        while len(data) > 0:
            candidate = data.pop()
            for comb in data:
                if candidate[0:i] == comb[0:i] and comb[i] not in candidate:
                    X1.append([])
                    X1[len(X1) - 1] = candidate[:]
                    X1[len(X1) - 1].append(comb[i])
                    X1[len(X1) - 1] = sorted(X1[len(X1) - 1])
                    if X1[len(X1) - 1] in X1[0:len(X1) - 1]:
                        del X1[-1]
                    else:
                        # 13: for %q & Xi+1 do
                        # 14: if q is a super sequence of any v & Vi then
                        # 15: Remove q from Xi+1;
                        for v in violating[i]:
                            if len(X1) == 0:
                                break
                            if all(elem in X1[len(X1) - 1] for elem in v):
                                del X1[-1]
        return X1


    def foo_relative(self,q,data,i,X1,violating):
        Z1 = self.X1_generator_relative(data, i, X1, violating)
        q.put(Z1)

    def foo_seq(self,q,data,i,X1,violating):
        Z1 = self.X1_generator_seq(data,i,X1,violating)
        q.put(Z1)

    def w_create(self, w, i, X1, violating, L, multiprocess):
        X1_new = []
        if self.bk_type == 'relative':  #sequence time
            if multiprocess:
                workers = int(len(w[i]) / 1000) + 1
                data_chunks = self.chunkIt(w[i], workers)
                mp.set_start_method('spawn')
                jobs = []
                for worker in range(workers):
                    print("In worker %d out of %d" %(worker+1, workers))
                    q = mp.Queue()
                    p = mp.Process(target=self.foo_relative, args=(q, data_chunks[worker], i, X1, violating))
                    jobs.append(p)
                    p.start()
                    X1_new += q.get()

                for job in jobs:
                    job.join()
            else:
                X1_new = self.X1_generator_relative(w[i], i, X1, violating)

        elif self.bk_type == 'sequence': #sequence
            if multiprocess:
                workers = int(len(w[i]) / 1000) + 1
                data_chunks = self.chunkIt(w[i], workers)
                mp.set_start_method('spawn')
                jobs = []
                for worker in range(workers):
                    print("In worker %d out of %d" %(worker+1, workers))
                    q = mp.Queue()
                    p = mp.Process(target=self.foo_seq, args=(q, data_chunks[worker],i,X1,violating))
                    jobs.append(p)
                    p.start()
                    X1_new += q.get()

                for job in jobs:
                    job.join()
            else:
                X1_new = self.X1_generator_seq(w[i],i,X1,violating)

        elif self.bk_type == 'multiset': #multiset
            X1_new = self.X1_generator_multiset(w[i],i,X1,violating)

        elif self.bk_type == 'set': #set
            X1_new = self.X1_generator_set(w[i],i,X1,violating)


        return X1_new

    def w_violating(self,gen,count,violating,prob, K,C,w, i):
        if i == 0:
            for q in gen:
                # 6: if |T(q)|< K or P(s|q) > C then
                if count[q] < K:
                    violating[0].append([q])
                else:
                    highestC = 0
                    for s in self.sensitive:
                        if highestC > C:
                            break
                        if prob[q][s] > highestC:
                            highestC = prob[q][s]
                    # 7: Add q to Vi;
                    if highestC > C:
                        violating[0].append([q])
                    # 8: else
                    # 9: Add q to Wi;
                    else:
                        w[0].append(q)
        else:
            for q in gen:
                # 6: if |T(q)|< K or P(s|q) > C then
                if count[tuple(q)] < K:
                    violating[i].append(q)
                else:
                    highestC = 0
                    for s in self.sensitive:
                        if highestC > C:
                            break
                        if prob[tuple(q)][s] > highestC:
                            highestC = prob[tuple(q)][s]
                    # 7: Add q to Vi;
                    if highestC > C:
                        violating[i].append(q)
                    # 8: else
                    # 9: Add q to Wi;
                    else:
                        w[i].append(q)
        return w, violating

    def prob(self, X1, count, el_trace, prob, i, type,first=False):
        if first:
            for q in X1:
              #creating prob(q|s) and count(q)
                for key, value in self.logsimple.items():
                    tr = value["trace"]
                    S = value["sensitive"]
                    if self.bk_type == 'set': #or self.bk_type == 'multiset':
                        if all(elem in tr for elem in q):
                            count[tuple(q)] += 1
                            el_trace[tuple(q)].append(value)
                            #listing all values of the different sensitive attributes (key2)
                            for key2, value2 in S.items():
                                prob[tuple(q)][key2].append(value2)
                    #new multiset (real)
                    elif self.bk_type == 'multiset':
                        for elem in q:
                            for ev in tr:
                                if elem[0] == ev[0] and elem[1] <= ev[1]:
                                    count[tuple(q)] += 1
                                    el_trace[tuple(q)].append(value)
                                    # listing all values of the different sensitive attributes (key2)
                                    for key2, value2 in S.items():
                                        prob[tuple(q)][key2].append(value2)

                    else:
                        included = False
                        for j in range(0, len(q)):
                            if j == 0:
                                if q[j] in tr:
                                    index = tr.index(q[j])
                                else:
                                    break
                            else:
                                if q[j] in tr[index + 1::]:
                                    index = tr.index(q[j])
                                    if j == len(q) - 1:
                                        included = True
                                        break
                                else:
                                    break
                            # if all(elem in X1[len(X1) - 1] for elem in v):
                        if included:
                            count[tuple(q)] += 1
                            el_trace[tuple(q)].append(value)
                            # listing all values of the different sensitive attributes (key2)
                            for key2, value2 in S.items():
                                prob[tuple(q)][key2].append(value2)
                #calculating the distribution of s for q
            for q in X1:
                prob = self.sens_boxplot(prob, count, q, i)
        else: # first is false
            if i == 0:
                for key, value in self.logsimple.items():
                  #creating prob(q|s) and count(q)
                    for q in X1:
                        tr = value["trace"]
                        S = value["sensitive"]
                        if q in tr:
                            count[q] += 1
                            el_trace[q].append(value)
                            #listing all values of the different sensitive attributes (key2)
                            for key2, value2 in S.items():
                                prob[q][key2].append(value2)
                    #calculating the distribution of s for q
                for q in X1:
                    prob = self.sens_boxplot(prob, count, q, i)
            else:
                newel_trace = {tuple(el): [] for el in X1}
                if not (self.bk_type == 'set' or self.bk_type == 'multiset'):
                    for q in X1:
                        if len(q) == 2:
                            for value in el_trace[q[0]]:
                                tr = value["trace"]
                                S = value["sensitive"]
                                included = True
                                if self.bk_type == 'sequence':
                                    if q[i] not in tr[tr.index(q[0])+1::]:
                                        included = False
                                else:
                                    if q[i] not in tr:
                                        included = False
                                if included:
                                    count[tuple(q)] += 1
                                    newel_trace[tuple(q)].append(value.copy())
                                    for key2, value2 in S.items():
                                        if type(prob[tuple(q)][key2]) is list:
                                            prob[tuple(q)][key2].append(value2)
                        else:
                            # if tuple(q[0:i]) not in el_trace.keys():
                            #     print(el_trace)
                            # else:
                            for value in el_trace[tuple(q[0:i])]:
                                tr = value["trace"]
                                S = value["sensitive"]
                                included = True
                                if self.bk_type == 'sequence':
                                    #if something went wrong
                                    if q[i-1] not in tr:
                                        included = False
                                    elif q[i] not in tr[tr.index(q[i-1]) + 1::]:
                                        included = False
                                else:
                                    if q[i] not in tr:
                                        included = False
                                if included:
                                    count[tuple(q)] += 1
                                    newel_trace[tuple(q)].append(value.copy())
                                    for key2, value2 in S.items():
                                        if type(prob[tuple(q)][key2]) is list:
                                            prob[tuple(q)][key2].append(value2)
                        prob = self.sens_boxplot(prob, count, q, i)
                else: # type is set or multiset
                    for key, value in self.logsimple.items():
                        for q in X1:
                            if len(q) == 2:
                                tr = value["trace"]
                                S = value["sensitive"]
                                included = True
                                for j in range(0,len(q)):
                                    if q[j][0] not in [ev[0] for ev in tr]:
                                        included = False
                                        break
                                    #new multiset
                                    elif self.bk_type == 'multiset':
                                        for ev in tr:
                                            if q[j][0] == ev[0] and q[j][1] > ev[1]:
                                                included = False
                                                break
                                if included:
                                    count[tuple(q)] += 1
                                    newel_trace[tuple(q)].append(value.copy())
                                    for key2, value2 in S.items():
                                        if type(prob[tuple(q)][key2]) is list:
                                            prob[tuple(q)][key2].append(value2)
                            else: #len q > 2
                                tr = value["trace"]
                                S = value["sensitive"]
                                included = True
                                for j in range(0, len(q)):
                                    # if q[j] not in tr:
                                    #     included = False
                                    #     break
                                    if q[j][0] not in [ev[0] for ev in tr]:
                                        included = False
                                        break
                                        # new multiset
                                    elif self.bk_type == 'multiset':
                                        for ev in tr:
                                            if q[j][0] == ev[0] and q[j][1] > ev[1]:
                                                included = False
                                                break
                                if included:
                                    count[tuple(q)] += 1
                                    newel_trace[tuple(q)].append(value.copy())
                                    for key2, value2 in S.items():
                                        if type(prob[tuple(q)][key2]) is list:
                                            prob[tuple(q)][key2].append(value2)
                    for q in X1:
                        prob = self.sens_boxplot(prob, count, q, i)
                el_trace = newel_trace.copy()
        return prob, count, el_trace

    def sens_boxplot(self, prob, count, q, i):
        if i == 0:
            # calculating the distribution of s for q
            for key in self.sensitive:
                highest = 0
                if key in self.cont:
                    freq = {"low": 0, "middle": 0, "high": 0}
                    lower_quartile = np.percentile(prob[q][key], 25)
                    higher_quartile = np.percentile(prob[q][key], 75)
                else:
                    freq = {v: 0 for v in prob[q][key]}
                for item in prob[q][key]:
                    # continious variables are handled with standard deviation
                    if key in self.cont:
                        if item < lower_quartile:
                            freq["low"] += 1
                        elif item > higher_quartile:
                            freq["high"] += 1
                        else:
                            freq["middle"] += 1
                    else:
                        if item in freq:
                            freq[item] += 1
                        else:
                            freq[item] = 1
                # Calculate confidence (C) which is mean of the category confidences,
                # where confidence of each category is 1/(No. values in the category).
                if key in self.cont:
                    if freq["low"] > 0:
                        low = 1 / freq["low"]
                    else:
                        low = 0
                    if freq["middle"] > 0:
                        middle = 1 / freq["middle"]
                    else:
                        middle = 0
                    if freq["high"]:
                        high = 1 / freq["high"]
                    else:
                        high = 0
                    highest = (low + middle + high) / 3
                else:
                    for item in prob[q][key]:
                        newhighest = freq[item] / count[q]
                        if newhighest > highest:
                            highest = newhighest
                prob[q][key] = highest
        else:
            for key in self.sensitive:
                highest = 0
                if prob[tuple(q)][key] == []:
                    prob[tuple(q)][key] = 0
                    continue
                if key in self.cont:
                    freq = {"low": 0, "middle": 0, "high": 0}
                    lower_quartile = np.percentile(prob[tuple(q)][key], 25)
                    higher_quartile = np.percentile(prob[tuple(q)][key], 75)
                else:
                    if type(prob[tuple(q)][key]) is not list:
                        continue
                    freq = {v: 0 for v in prob[tuple(q)][key]}
                for item in prob[tuple(q)][key]:
                    # continious variables are handled with standard deviation
                    if key in self.cont:
                        if item < lower_quartile:
                            freq["low"] += 1
                        elif item > higher_quartile:
                            freq["high"] += 1
                        else:
                            freq["middle"] += 1
                    else:
                        if item in freq:
                            freq[item] += 1
                        else:
                            freq[item] = 1
                # Calculate confidence (C) which is mean of the category confidences,
                # where confidence of each category is 1/(No. values in the category).
                if key in self.cont:
                    if freq["low"] > 0:
                        low = 1 / freq["low"]
                    else:
                        low = 0
                    if freq["middle"] > 0:
                        middle = 1 / freq["middle"]
                    else:
                        middle = 0
                    if freq["high"]:
                        high = 1 / freq["high"]
                    else:
                        high = 0
                    highest = (low + middle + high) / 3
                else:
                    for item in prob[tuple(q)][key]:
                        newhighest = freq[item] / count[tuple(q)]
                        if newhighest > highest:
                            highest = newhighest
                prob[tuple(q)][key] = highest
        return prob



