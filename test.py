# li = [844000, 60000, 73000, 24000, 157000, 1001000]
# li = [844, 60, 73, 24, 157, 1001]
# li = [1,1]
li = [3700, 65, 3765, 1, 1, 1, 3]

def elemental_list(li):
    '''
    pick the last element
    sum the previous elements
    check if it equals the last element of the splited list
    if not, contiue the sum unitl the last element
    '''
    
    li_copy = li.copy()
    ## remove sub-totals
    for idx, x in enumerate(li):
        check_idx = -idx - 1
        check_li, check_total = li[:check_idx], li[check_idx]
        check_sum = 0
        for i in check_li[::-1]:
            check_sum += i
            if check_sum == check_total:
                print(f'found a subtotal: {check_total}')
                # print(f'found a subtotal: {check_idx}')
                li_copy.remove(check_total)
                break
    
    # remove totals
    if sum(li_copy[:-1]) == li_copy[-1]:
            if len(li_copy) > 3:
                li_copy.pop(-1)
    return li_copy
    
print(elemental_list(li))
