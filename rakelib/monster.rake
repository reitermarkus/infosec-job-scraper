# frozen_string_literal: true

# Module for scraping jobs from https://monster.at.
module Monster
  def search(query)
    query_params = URI.encode_www_form(q: query.gsub(/\s+/, '-'), cy: 'at')
    url = "https://www.monster.at/jobs/suche/?#{query_params}"
    log.debug url
    get(url)

    log.debug 'Looking for “cookie” button …'
    cookie_button = find_element(css: '#cookie-modal a[href="#cookie-modal"]')
    execute_script('arguments[0].click();', cookie_button)

    loop do
      log.debug 'Looking for “Load more jobs” button …'
      load_more_jobs_button = find_element(id: 'loadMoreJobs')

      begin
        execute_script('arguments[0].click();', load_more_jobs_button)
      rescue Selenium::WebDriver::Error::StaleElementReferenceError
        # Button may disappear because scrolling triggers auto-loading.
      end

      log.debug 'Loading more jobs …'
    rescue Selenium::WebDriver::Error::NoSuchElementError
      log.debug 'No more jobs.'
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

    details[:location] = details.delete('Standort')
    details[:contract_type] = details.delete('Vertragsart')

    details[:title] = find_element(css: '#JobViewHeader .title').text.strip

    begin
      details[:subtitle] = find_element(css: '#JobViewHeader .subtitle').text.strip
    rescue Selenium::WebDriver::Error::NoSuchElementError
      # Some pages may only contain the main title.
    end

    body = begin
             iframe = find_element(id: 'JobPreviewSandbox')

             switch_to.frame(iframe)

             find_element(tag_name: 'body')
           rescue Selenium::WebDriver::Error::NoSuchElementError
             find_element(id: 'JobPreview')
           end

    details[:body] = body.attribute('innerHTML')

    details
  rescue Selenium::WebDriver::Error::NoSuchElementError => e
    begin
      find_element(id: 'NotAvailAlert')
      log.error 'Page unavailable.'
      nil
    rescue Selenium::WebDriver::Error::NoSuchElementError
      # Raise the previous exception if the current page
      # is not the “job unavailable” page.
      raise e
    end
  end
end

task :monster do
  get_jobs(Monster)
end
