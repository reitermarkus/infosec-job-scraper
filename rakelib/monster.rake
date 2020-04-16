# frozen_string_literal: true

# Module for scraping jobs from https://monster.at.
module Monster
  def search(query)
    query_params = URI.encode_www_form(q: query.gsub(/\s+/, '-'), cy: 'at')
    url = "https://www.monster.at/jobs/suche/?#{query_params}"
    get(url)

    puts 'Looking for “cookie” button …'
    cookie_button = find_element(css: '#cookie-modal a[href="#cookie-modal"]')
    execute_script('arguments[0].click();', cookie_button)

    loop do
      puts 'Looking for “Load more jobs” button …'

      load_more_jobs_button = find_element(id: 'loadMoreJobs')

      begin
        execute_script('arguments[0].click();', load_more_jobs_button)
      rescue Selenium::WebDriver::Error::StaleElementReferenceError
        # Button may disappear because scrolling triggers auto-loading.
      end

      puts 'Loading more jobs …'
    rescue Selenium::WebDriver::Error::NoSuchElementError
      puts 'No more jobs.'
      break
    end

    find_elements(css: '#SearchResults .card-header .title a[href]')
      .map { |l| l.attribute('href') }
      .to_set
  end

  def get_detail_page(url)
    get(url)

    keys = find_elements(css: '#JobSummary .key').map { |e| e&.text&.strip }
    values = find_elements(css: '#JobSummary .value').map { |e| e&.text&.strip }

    details = keys.zip(values).to_h

    details[:title] = find_element(css: '#JobViewHeader .title').text.strip
    details[:subtitle] = find_element(css: '#JobViewHeader .subtitle').text.strip

    body = begin
             iframe = find_element(id: 'JobPreviewSandbox')

             switch_to.frame(iframe)

             find_element(tag_name: 'body')
           rescue Selenium::WebDriver::Error::NoSuchElementError
             find_element(id: 'JobPreview')
           end

    details[:body] = body.attribute('innerHTML')

    details
  end
end

task :monster do
  get_jobs(Monster)
end
