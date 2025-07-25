import re
from difflib import SequenceMatcher

def find_best_match_offset_advanced(needle, haystack, case_sensitive=True, allow_partial=True):
  print("Calling find_best_match_offset_advanced")
  print("NEEDLE:", needle)
  print("HAYSTACK:", haystack, flush=True)
  """
  Advanced version that can handle different length matches and partial matches.

  Args:
    needle (str): Text to search for
    haystack (str): Text to search in
    case_sensitive (bool): Whether to perform case-sensitive matching
    allow_partial (bool): Whether to allow partial matches of different lengths

  Returns:
    tuple: (offset, matched_text, similarity_ratio)
  """
  if not needle or not haystack:
    return (0, "", 0.0)

  # Handle case sensitivity
  search_needle = needle if case_sensitive else needle.lower()
  search_haystack = haystack if case_sensitive else haystack.lower()

  needle_len = len(search_needle)
  haystack_len = len(search_haystack)

  best_ratio = 0
  best_offset = 0
  best_match_text = ""

  if allow_partial:
    # Try different substring lengths around the needle length
    min_len = max(1, needle_len // 2)
    max_len = min(haystack_len, needle_len * 2)

    for length in range(min_len, max_len + 1):
      for i in range(haystack_len - length + 1):
        substring = search_haystack[i:i + length]
        ratio = SequenceMatcher(None, search_needle, substring).ratio()

        if ratio > best_ratio:
          best_ratio = ratio
          best_offset = i
          best_match_text = haystack[i:i + length]
  else:
    # Fixed length matching (original approach)
    if needle_len > haystack_len:
      return (0, haystack, SequenceMatcher(None, search_needle, search_haystack).ratio())

    for i in range(haystack_len - needle_len + 1):
      substring = search_haystack[i:i + needle_len]
      ratio = SequenceMatcher(None, search_needle, substring).ratio()

      if ratio > best_ratio:
        best_ratio = ratio
        best_offset = i
        best_match_text = haystack[i:i + needle_len]

  return (best_offset, best_match_text, best_ratio)

def fix_header(patch, orig, header_start, header_end, hunk_start, hunk_end, prev_additions, prev_deletions):
  hunk = patch[hunk_start:hunk_end]
  additions = re.findall(r'(?m)^\+(.*)$', hunk)
  deletions = re.findall(r'(?m)^-(.*)$', hunk)
  temp = re.sub(r'(?m)^-', "", hunk)
  temp2 = re.sub(r'(?m)^\+.*$\n?', "", temp)
  approx_orig = temp2[1:].replace('\n ', '\n') if temp2[0] == ' ' else temp2
  offset, match, sim_ratio = find_best_match_offset_advanced(approx_orig, orig)
  print(f"Best match: offset={offset}, match={match}, sim_ratio={sim_ratio}")
  orig_start = orig[:offset].count('\n') + 1
  new_start = orig_start + prev_additions - prev_deletions
  orig_len = hunk.count('\n')
  new_len = orig_len + len(additions) - len(deletions)
  new_header = f"@@ -{orig_start},{orig_len} +{new_start},{new_len} @@"
  new_patch = patch[:header_start] + new_header + patch[header_end:]
  return new_patch, len(additions), len(deletions)

# `patch` is a unidiff to be applied to `orig`
# TODO actually I think this works for context diffs too
# FIXME make this less brittle
def fix_hunk_offsets(patch, orig):
  # headers_re = r'(?m)^@@ -(\d+),(\d+) \+(\d+),(\d+) @@\s*$'
  # headers_re = r'(?m)^@@ [^@]* @@\s*$'
  headers_re = r'(?m)^@@.*$'
  if re.search(headers_re, orig):
    raise ValueError("Original must not contain '@@ ... @@'")

  prev_additions = 0
  prev_deletions = 0
  hunk_headers = list(re.finditer(headers_re, patch))
  if len(hunk_headers) == 0:
    raise ValueError("No headers")

  for i in range(len(hunk_headers) - 1):
    header_start = hunk_headers[i].start()
    header_end = hunk_headers[i].end()
    hunk_start = header_end + 1
    hunk_end = hunk_headers[i+1].start() - 2
    patch, num_additions, num_deletions = fix_header(
      patch, orig, header_start, header_end, hunk_start,
      hunk_end, prev_additions, prev_deletions)
    prev_additions += num_additions
    prev_deletions += num_deletions

  header_start = hunk_headers[-1].start()
  header_end = hunk_headers[-1].end()
  hunk_start = header_end + 1
  hunk_end = len(patch) - 2
  patch, num_additions, num_deletions = fix_header(
    patch, orig, header_start, header_end, hunk_start,
    hunk_end, prev_additions, prev_deletions)
  prev_additions += num_additions
  prev_deletions += num_deletions

  return patch
