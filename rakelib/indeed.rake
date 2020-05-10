# frozen_string_literal: true

# Module for scraping jobs from https://at.indeed.com.
module Indeed
  def search(query)
    jobs = Set.new

    page = 0
    max_page = 1

    log.debug 'Looking for pages …'

    while page <= max_page
      query_params = URI.encode_www_form(q: query, start: page * 10)
      url = "https://at.indeed.com/Jobs?#{query_params}"
      log.debug url
      get(url)

      jobs += find_elements(css: '#resultsBodyContent .jobsearch-SerpJobCard .title a[href]')
              .map { |l| l.attribute('href') }

      pages = find_element(css: '#resultsBodyContent .pagination').text.scan(/\d+/).map(&:to_i)
      log.debug "Pages: #{pages}"

      page += 1
      max_page = [max_page, *pages].max
    end

    jobs
  end

  def get_detail_page(url)
    get(url)

    title = find_element(css: '.jobsearch-ViewJobLayout-jobDisplay .jobsearch-JobInfoHeader-title')
    location = begin
      find_element(css: '.jobsearch-JobMetadataHeader-itemWithIcon .icl-IconFunctional--location + .jobsearch-JobMetadataHeader-iconLabel')
        .text.strip
    rescue Selenium::WebDriver::Error::NoSuchElementError
      nil
    end
    contract_type = begin
      find_element(css: '.jobsearch-JobMetadataHeader-itemWithIcon .icl-IconFunctional--jobs + .jobsearch-JobMetadataHeader-iconLabel')
        .text.strip
    rescue Selenium::WebDriver::Error::NoSuchElementError
      nil
    end
    body = find_element(id: 'jobDescriptionText')

    details = {
      title: title.text.strip,
      location: location,
      contract_type: contract_type,
      body: body.attribute('innerHTML'),
    }

    details
  end
end

task :indeed do
  get_jobs(Indeed)
end
