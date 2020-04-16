# frozen_string_literal: true

require 'date'
require 'pathname'
require 'json'
require 'digest'
require 'set'
require 'selenium-webdriver'

DATA_DIR = Pathname(__dir__).join('data')

def headless?
  !ENV['HEADLESS'].nil?
end

def driver
  driver = if (remote_url = ENV['REMOTE_WEBDRIVER_URL'])
    Selenium::WebDriver.for(:remote, url: remote_url, desired_capabilities: :firefox)
  else
    options = Selenium::WebDriver::Firefox::Options.new(args: [*(headless? ? '--headless' : nil)])
    Selenium::WebDriver.for(:firefox, options: options)
  end

  driver.manage.timeouts.implicit_wait = 5
  driver.manage.window.size = Selenium::WebDriver::Dimension.new(1280, 1024)
  driver
end

# Module for scraping jobs from https://at.indeed.com.
module Indeed
  def search(query)
    jobs = Set.new

    page = 0
    max_page = 1

    while page <= max_page
      query_params = URI.encode_www_form(q: query, start: page * 10)
      get("https://at.indeed.com/Jobs?#{query_params}")

      jobs += find_elements(css: '#resultsBodyContent .jobsearch-SerpJobCard .title a[href]')
              .map { |l| l.attribute('href') }

      puts 'Looking for pages …'
      pages = find_element(css: '#resultsBodyContent .pagination').text.scan(/\d+/).map(&:to_i)
      puts "Pages: #{pages}"

      page += 1
      max_page = [max_page, *pages].max
    end

    jobs
  end

  def get_detail_page(url)
    get(url)

    title = find_element(css: '.jobsearch-ViewJobLayout-jobDisplay .jobsearch-JobInfoHeader-title')
    body = find_element(id: 'jobDescriptionText')

    details = {
      title: title.text.strip,
      body: body.attribute('innerHTML'),
    }

    details
  end
end

# Module for scraping jobs from https://monster.at.
module Monster
  def search(query)
    query_params = URI.encode_www_form(q: query.gsub(/\s+/, '-'), cy: 'at')
    get("https://www.monster.at/jobs/suche/?#{query_params}")

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

    keys = find_elements(css: '#JobSummary .key').map(&:text).map(&:strip)
    values = find_elements(css: '#JobSummary .value').map(&:text).map(&:strip)

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

# Module for scraping jobs from https://stepstone.at.
module StepStone
  def search(query)
    jobs = Set.new

    page = 0
    max_page = 1

    while page <= max_page
      query_params = URI.encode_www_form(ke: query, fu: 1_000_000, li: 100, of: page * 100)
      get("https://www.stepstone.at/5/ergebnisliste.html?#{query_params}")

      jobs += find_elements(css: '#dynamic-resultlist a[href^="/stellenangebote-"]')
              .map { |l| l.attribute('href') }

      puts 'Looking for pages …'
      pages = find_element(css: '#dynamic-resultlist [class*="PaginationWrapper"]')
              .text.scan(/\d+/).map(&:to_i)
      puts "Pages: #{pages}"

      page += 1
      max_page = [max_page, *pages].max
    end

    jobs
  end

  def get_detail_page(url)
    get(url)

    title = find_element(css: '.listing__job-title')
    body = find_element(css: '.js-app-ld-ContentBlock')

    details = {
      title: title.text.strip,
      body: body.attribute('innerHTML'),
    }

    details
  end
end

def get_jobs(driver, mod)
  driver.extend(mod)

  puts "Looking for jobs on #{mod.name} …"
  jobs = driver.search('information security')
  puts "Found #{jobs.count} jobs on #{mod.name}."

  jobs.each do |url|
    puts "Fetching “#{url}” …"

    details = driver.get_detail_page(url)
    details[:url] = url
    details[:date] = Date.today.iso8601

    file = DATA_DIR.join("#{mod.name.downcase}-#{Digest::SHA2.hexdigest(url)}.json")
    file.dirname.mkpath
    file.write JSON.pretty_generate(details)
    puts "Saved #{file}."
  end
ensure
  driver.quit
end

task :monster do
  get_jobs(driver, Monster)
end

task :indeed do
  get_jobs(driver, Indeed)
end

task :stepstone do
  get_jobs(driver, StepStone)
end

task default: %i[indeed monster stepstone]
