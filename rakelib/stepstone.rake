# frozen_string_literal: true

# Module for scraping jobs from https://stepstone.at.
module StepStone
  def search(query)
    jobs = Set.new

    page = 0
    max_page = 1

    get('https://www.stepstone.at/')

    log.debug 'Looking for pages …'

    while page < max_page
      query_params = URI.encode_www_form(
        ke: query,
        fu: 1_000_000,
        li: 100,
        **(page.positive? ? { of: page * 100 } : {})
      )
      url = "https://www.stepstone.at/5/ergebnisliste.html?#{query_params}"
      log.debug url
      get(url)

      jobs += find_elements(css: '#dynamic-resultlist a[href^="/stellenangebote-"]')
              .map { |l| l.attribute('href') }

      pages = find_element(css: '#dynamic-resultlist [class*="PaginationWrapper"]')
              .text.scan(/\d+/).map(&:to_i)
      log.debug "Pages: #{pages}"

      page += 1
      max_page = [max_page, *pages].max
    end

    jobs
  end

  def get_detail_page(url)
    get(url)

    title = find_element(css: '.js-listing-header .at-header-company-jobTitle')
    location = find_element(css: '.js-listing-header .at-listing__list-icons_location')
    contract_type = find_element(css: '.js-listing-header .at-listing__list-icons_contract-type')
    work_type = find_element(css: '.js-listing-header .at-listing__list-icons_work-type')

    body = find_element(css: '.js-app-ld-ContentBlock')

    details = {
      title: title.text.strip,
      location: location.text.strip,
      contract_type: "#{work_type.text.strip}, #{contract_type.text.strip}",
      body: body.attribute('innerHTML'),
    }

    details
  end
end

task :stepstone do
  get_jobs(StepStone)
end
