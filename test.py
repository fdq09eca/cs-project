
# import pdfplumber, requests
# from io import BytesIO

# # url, p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0717/2020071700849.pdf', 90
# url , p = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2019/1028/ltn20191028063.pdf', 20 # 2cols, correct!!

# def divide_into_two_cols(page, d=0.5):
#     l0, l1 = 0 * float(page.width), d * float(page.width)
#     r0, r1 = d * float(page.width), 1 * float(page.width)
#     top, bottom = 0, float(page.height)
#     l_bbx = (l0, top, l1, bottom)
#     r_bbx = (r0, top, r1, bottom)
#     left_col = page.within_bbox(l_bbx, relative = True)
#     right_col = page.within_bbox(r_bbx, relative = True)
#     return left_col, right_col

# with requests.get(url) as response:
#     response.raise_for_status()
#     io_obj = BytesIO(response.content)
#     pdf = pdfplumber.open(io_obj)
#     page = pdf.pages[p]
#     print(page.extract_text())
#     left_col, right_col = divide_into_two_cols(page)
#     print(left_col.chars == right_col.chars)

# # li = [844000, 60000, 73000, 24000, 157000, 1001000]
# # li = [844, 60, 73, 24, 157, 1001]
# # li = [1,1]
# li = [3700, 65, 3765, 1, 1, 1, 3]

# def elemental_list(li):
#     '''
#     pick the last element
#     sum the previous elements
#     check if it equals the last element of the splited list
#     if not, contiue the sum unitl the last element
#     '''
    
#     li_copy = li.copy()
#     ## remove sub-totals
#     for idx, x in enumerate(li):
#         check_idx = -idx - 1
#         check_li, check_total = li[:check_idx], li[check_idx]
#         check_sum = 0
#         for i in check_li[::-1]:
#             check_sum += i
#             if check_sum == check_total:
#                 print(f'found a subtotal: {check_total}')
#                 # print(f'found a subtotal: {check_idx}')
#                 li_copy.remove(check_total)
#                 break
    
#     # remove totals
#     if sum(li_copy[:-1]) == li_copy[-1]:
#             if len(li_copy) > 3:
#                 li_copy.pop(-1)
#     return li_copy
    
# print(elemental_list(li))
