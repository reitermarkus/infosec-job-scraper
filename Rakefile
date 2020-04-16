# frozen_string_literal: true

require 'date'
require 'pathname'
require 'json'
require 'digest'
require 'set'
require 'selenium-webdriver'
require 'selenium/webdriver/remote/http/persistent'

DATA_DIR = Pathname(__dir__).join('data')

module EnvExtension
  def headless?
    !self['HEADLESS'].nil?
  end
end

ENV.extend(EnvExtension)

# WebDriver wrapper, allowing for connection reset.
class Driver < Delegator
  def initialize
    __setobj__ begin
      driver = if (remote_url = ENV['REMOTE_WEBDRIVER_URL'])
        Selenium::WebDriver.for(:remote, url: remote_url, desired_capabilities: :firefox)
      else
        options = Selenium::WebDriver::Firefox::Options.new(args: [*(ENV.headless? ? '--headless' : nil)])
        Selenium::WebDriver.for(:firefox, options: options)
      end
      driver.manage.timeouts.implicit_wait = 5
      driver.manage.window.size = Selenium::WebDriver::Dimension.new(1280, 1024)
      driver
    end
  end

  def __getobj__
    @driver
  end

  def __setobj__(obj)
    @driver = obj
  end

  def reset(t = nil)
    quit rescue nil
    sleep t if t
    initialize
  end
end

def driver
  @driver ||= Driver.new
end

def with_retry(*exceptions)
  tries ||= 0
  yield
rescue *exceptions => e
  $stderr.puts "#{e.class}: #{e}"
  driver.reset 2**tries

  tries += 1
  $stderr.puts "Would raise: #{e}" if tries > 3
  # raise if tries > 3

  $stderr.puts "Retrying (#{tries}) …"
  retry
end

def get_jobs(mod)
  driver.extend(mod)

  puts "Looking for jobs on #{mod.name} …"
  jobs = with_retry Selenium::WebDriver::Error::NoSuchWindowError, Selenium::WebDriver::Error::UnknownError do
    driver.search('information security')
  end
  puts "Found #{jobs.count} jobs on #{mod.name}."

  jobs.each do |url|
    puts "Fetching “#{url}” …"

    details = with_retry Selenium::WebDriver::Error::NoSuchWindowError, Selenium::WebDriver::Error::UnknownError do
      driver.get_detail_page(url)
    end
    details[:url] = url
    details[:date] = Date.today.iso8601

    file = DATA_DIR.join("#{mod.name.downcase}-#{Digest::SHA2.hexdigest(url)}.json")
    file.dirname.mkpath
    file.write JSON.pretty_generate(details)

    puts "Saved #{file}."
  end
end

task default: %i[indeed stepstone monster]
