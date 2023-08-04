from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import re
import arxiv
import argparse
import pandas as pd
from tqdm import tqdm



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--link', help='ar5iv link of paper')
    args = parser.parse_args()
    
    driver = webdriver.Chrome()
    driver.get(args.link)
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH,'//*[@id="bib"]/ul/li')))
    references = driver.find_elements(By.XPATH,'//*[@id="bib"]/ul/li')
    results = []
    for ref in tqdm(references,desc="Fetching the arxiv link"):
        span = ref.find_elements(By.XPATH,"span")
        author = span[0].text.split(" ")[0]
        title = re.sub('[^a-zA-Z0-9 \n\.]', ' ', span[2].text)
        query = f"au:{author} AND ti:{title}"
        # print(query)
        search = arxiv.Search(query=query,max_results=5)
        found = False;
        for result in search.results():
            if(span[2].text.lower()[:-5] in result.title.lower() ):
                results.append(result)
                found = True;
                break;
        if not found:
            print(f"{query} not found")
        
    df = pd.DataFrame(columns=["title","published","updated","arxiv_link","references","citations","code_links"])          
    for idx,result in tqdm(enumerate(results),desc="Searching for the code",total=len(results)):
        paper_dict = {}
        
        # paper_list["title"].append(result.title.lower())
        paper_dict["title"] = result.title
        paper_dict["published"] = result.published.date().isoformat()
        paper_dict["updated"] = result.updated.date().isoformat()
        paper_dict["arxiv_link"] = result.entry_id
        
        try:
        
            driver.get(result.entry_id)    
            
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="labstabs"]/div/label[1]')))
            ref_tab = driver.find_element(By.XPATH, '//*[@id="labstabs"]/div/label[1]')
            ref_tab.click()
            
            if not idx:
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bibex-toggle"]/following-sibling::span')))
                ref_toggle = driver.find_element(By.XPATH, '//*[@id="bibex-toggle"]/following-sibling::span')
                ref_toggle.click()
            
            try:
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'bib-col-title')))
                count = driver.find_elements(By.CLASS_NAME, 'bib-col-title')
                for ele in count:
                    # paper_list["count"].append((ele.text))
                    splits = ele.text.split("(")
                    paper_dict[splits[0].strip().lower()] = splits[1][:-1]
            except:
                paper_dict["references"]  = 0 
                paper_dict["citations"] = 0
                
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="labstabs"]/div/label[2]')))
            code_tab = driver.find_element(By.XPATH, '//*[@id="labstabs"]/div/label[2]')
            code_tab.click()
            
            if not idx:
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="paperwithcode-toggle"]/following-sibling::span')))
                pwc = driver.find_element(By.XPATH, '//*[@id="paperwithcode-toggle"]/following-sibling::span')
                pwc.click()
            
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="pwc-output"]/p[*]/a ')))
                code_link = driver.find_elements(By.XPATH, '//*[@id="pwc-output"]/p[*]/a ')
                link = []
                for ele in code_link:
                    # paper_list.append((ele.get_attribute("href")))
                    link.append(ele.get_attribute("href"))
                paper_dict["code_links"]= link[0] if len(link) == 1 else link
                
            except:
                paper_dict["code_links"] = None
                print(f"{paper_dict['title']} code not found")
                
            df.loc[idx] = paper_dict
        except:
            print(f"Skipping {paper_dict['title']}...")
    df.to_csv("out.csv",index=False)