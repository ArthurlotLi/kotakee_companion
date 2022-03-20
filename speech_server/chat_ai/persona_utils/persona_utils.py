#
# persona_utils.py
#
# Small tools to help with gathering some fun data to provide to the
# chatbot. Should be called direclty. 

import json
import argparse 

class PersonaUtils:
  output_file = "extracted_lines.json"

  # The model WILL give up and die beyond 512. We will extract all
  # lines and then, from those lines, choose the lines with all
  # unique words first. 
  max_words_extracted = 512

  def __init__(self):
    pass

  # Given a keyword and a text file, go through the entire file and
  # retain all lines that have a specific keyword in them. Format 
  # them all and write to a json-formatted file in a manner
  # acceptable for preset_persona.json. 
  def extract_lines(self, keyword, input_file):
    source_file_lines = open(input_file).read().splitlines()
    extracted_lines = []
    written_lines = 0

    for line in source_file_lines:
      if keyword in line:
        # Formatting. 
        extracted_line = ""
        line = line.replace(keyword, "")
        line = line.strip()
        for word in line.split():
          if "(" not in word and ")" not in word:
            extracted_line = extracted_line + " " + word
        extracted_line = extracted_line.strip()

        extracted_lines.append(extracted_line)
        written_lines = written_lines + 1
    
    # Get unique lines first, then append the rest. 
    chosen_lines = []
    remaining_lines = []
    chosen_words_count = 0

    for extracted_line in extracted_lines:
      priority_line = True
      wordcount = len(extracted_line.split())
      if chosen_words_count < self.max_words_extracted and wordcount <= (self.max_words_extracted - chosen_words_count):
        for chosen_line in chosen_lines:
          for word in extracted_line.split():
            if priority_line is True and word in chosen_line.split():
              priority_line = False

        if priority_line is True:
          chosen_lines.append(extracted_line)
          chosen_words_count = chosen_words_count + wordcount
        else:
          remaining_lines.append(extracted_line)
    
    
    #while chosen_words_count < self.max_words_extracted:
      #chosen_lines.append(remaining_lines.pop())

    # Write the item to a json file. 
    with open(self.output_file, "w") as output_file:
      json.dump(chosen_lines, output_file, indent=2, ensure_ascii=False)

    print("[INFO] Extracted " + str(len(chosen_lines)) + " lines and " + str(chosen_words_count) + " words. Done!")

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("keyword")
  parser.add_argument("input_file")
  args = parser.parse_args()

  keyword = args.keyword
  input_file = args.input_file

  persona_utils = PersonaUtils()
  persona_utils.extract_lines(keyword=keyword, input_file=input_file)