# Todo

1. modify `get_page()`:
   1. check the if the page is landscape before processing
      1. if yes:
         1. get audit name, if it is none, then page number + 2 call `get_auditor()` again
   2. check if the page `cn_ratio`
      1. if *> 85%*:
         1. try to get the auditor, if it is none, then page number - 1, call `get_auditor` again
2. modify the `get_auditor()`
   1. write a function that read page from left to right
      1. Append matched case to a list and return the list as result.
      2. if None, read page from edges to middle (remove noise)
3. build a `validate_result()` for the passed cases
    1. check if similar result (>90% similarity) has been in the database
    2. if not, prompt the result and pdf url to the user, user decides if the result should be updated to the database
4. modify `get_toc`:
   1. if `search by outline`
      1. allow multiple target outline.
   2. if `search by pages`
      1. perform search for every page.
